import secrets
import logging

from django.conf import settings
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.utils import timezone
from datetime import timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from clubs.models import Club
from clubs.serializers import ClubSerializer
from bookings.models import Booking
from bookings.tasks import send_otp_sms_task, send_welcome_email_task

from .models import OTP
from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    UserUpdateSerializer,
    OTPVerifySerializer,
    ChangePasswordSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)


def generate_otp_code():
    """Cryptographically-secure 6-digit OTP (not random.randint)."""
    return str(secrets.randbelow(900000) + 100000)


class SendOTPView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    def post(self, request):
        mobile_number = request.data.get('mobile_number', '').strip()

        if not mobile_number or not mobile_number.isdigit() or len(mobile_number) != 10:
            return Response(
                {'error': 'Please enter a valid 10-digit mobile number'},
                status=status.HTTP_400_BAD_REQUEST
            )

        otp_code = generate_otp_code()

        with transaction.atomic():
            OTP.objects.filter(mobile_number=mobile_number).delete()
            OTP.objects.create(
                mobile_number=mobile_number,
                otp=otp_code,
                expires_at=timezone.now() + timedelta(minutes=10),
                ip_address=request.META.get('REMOTE_ADDR'),
            )

        # Always send asynchronously via Celery — never block the request
        # thread on a Twilio round-trip.
        send_otp_sms_task.delay(mobile_number, otp_code)

        logger.info(f"OTP requested for {mobile_number}")

        response_data = {
            'message': 'OTP sent successfully',
            'mobile_number': mobile_number,
            'expires_in': 600,
        }

        # NEVER return the raw OTP outside local development. Doing this in
        # production means anyone can "verify" without ever receiving an SMS.
        if settings.DEBUG:
            response_data['otp'] = otp_code

        return Response(response_data, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    # Verify OTP and return JWT token if user exists
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        mobile_number = serializer.validated_data['mobile_number']
        otp_code = serializer.validated_data['otp']

        otp = OTP.objects.filter(
            mobile_number=mobile_number,
            is_verified=False,
        ).order_by('-created_at').first()

        if otp is None:
            return Response({
                'error': 'Invalid OTP. Please check and try again.'
            }, status=status.HTTP_400_BAD_REQUEST)

        if otp.is_expired:
            otp.delete()
            return Response({
                'error': 'OTP has expired. Please request a new one.'
            }, status=status.HTTP_400_BAD_REQUEST)

        if otp.attempts >= OTP.MAX_ATTEMPTS:
            return Response({
                'error': 'Too many incorrect attempts. Please request a new OTP.'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        if otp.otp != otp_code:
            otp.register_failed_attempt()
            remaining = max(OTP.MAX_ATTEMPTS - otp.attempts, 0)
            return Response({
                'error': f'Invalid OTP. {remaining} attempt(s) remaining.'
            }, status=status.HTTP_400_BAD_REQUEST)

        otp.is_verified = True
        otp.save(update_fields=['is_verified'])

        try:
            user = User.objects.get(mobile_number=mobile_number)
            user.is_mobile_verified = True
            user.save(update_fields=['is_mobile_verified'])

            refresh = RefreshToken.for_user(user)
            logger.info(f"User {user.username} logged in via OTP")

            return Response({
                'message': 'OTP verified successfully',
                'user_exists': True,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            logger.info(f"OTP verified for new user: {mobile_number}")
            return Response({
                'message': 'OTP verified successfully. Please complete registration.',
                'user_exists': False,
                'mobile_number': mobile_number
            }, status=status.HTTP_200_OK)


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = serializer.save()
        except IntegrityError:
            logger.warning("Registration IntegrityError — likely a duplicate race", exc_info=True)
            return Response(
                {'error': 'An account with these details already exists.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        send_welcome_email_task.delay(user.id)

        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Registration successful',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'mobile_number': str(user.mobile_number),
                'is_staff': user.is_staff,
            }
        }, status=status.HTTP_201_CREATED)


class UserProfileView(APIView):
    # Get and update user profile
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"User {request.user.username} updated profile")
            return Response(UserSerializer(request.user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"User {request.user.username} updated profile")
            return Response(UserSerializer(request.user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    # Change user password
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        if not user.check_password(serializer.validated_data['old_password']):
            return Response({
                'error': 'Old password is incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()

        logger.info(f"User {user.username} changed password")

        return Response({
            'message': 'Password changed successfully'
        })


# ---------------------------------------------------------------------------
# Admin views
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAdminUser])
def dashboard_stats(request):
    from bookings.models import Booking
    from payments.models import Payment
    from clubs.models import Club, Sport
    from django.db.models import Sum

    today = timezone.now().date()

    total_bookings = Booking.objects.count()
    confirmed_bookings = Booking.objects.filter(status='confirmed').count()
    pending_bookings = Booking.objects.filter(status='pending').count()
    today_bookings = Booking.objects.filter(created_at__date=today).count()
    active_users = User.objects.filter(is_active=True, is_staff=False).count()

    total_earned = Payment.objects.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0
    total_refunded = Payment.objects.filter(status='refunded').aggregate(total=Sum('amount'))['total'] or 0
    net_revenue = float(total_earned) - float(total_refunded)

    weekly_bookings = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = Booking.objects.filter(created_at__date=day, status__in=['confirmed', 'pending', 'refunded']).count()
        weekly_bookings.append({'date': str(day), 'label': day.strftime('%a'), 'count': count})

    recent_activities = []

    for b in Booking.objects.select_related('user', 'club', 'sport').order_by('-updated_at')[:15]:
        if b.status == 'confirmed':
            msg = f"{b.user.get_full_name() or b.user.username} booked {b.sport.name} at {b.club.name}"
            atype = 'confirmed'
        elif b.status == 'refunded':
            msg = f"Refund for {b.user.get_full_name() or b.user.username} — {b.club.name}"
            atype = 'refunded'
        elif b.status == 'cancelled':
            msg = f"{b.user.get_full_name() or b.user.username} cancelled at {b.club.name}"
            atype = 'cancelled'
        elif b.status == 'pending':
            msg = f"{b.user.get_full_name() or b.user.username} initiated booking at {b.club.name}"
            atype = 'pending'
        else:
            continue
        delta = timezone.now() - b.updated_at
        ts = b.updated_at.strftime('%d %b, %I:%M %p')
        if delta.total_seconds() < 60:
            ts = "Just now"
        elif delta.total_seconds() < 3600:
            ts = f"{int(delta.total_seconds()//60)}m ago"
        elif delta.days == 0:
            ts = f"{int(delta.total_seconds()//3600)}h ago"
        recent_activities.append({'type': atype, 'message': msg, 'time': ts,
            'amount': float(b.amount) if b.status in ['confirmed', 'refunded'] else None,
            'sort_key': b.updated_at.timestamp()})

    for club in Club.objects.order_by('-created_at')[:5]:
        delta = timezone.now() - club.created_at
        ts = club.created_at.strftime('%d %b, %I:%M %p')
        if delta.total_seconds() < 60:
            ts = "Just now"
        elif delta.total_seconds() < 3600:
            ts = f"{int(delta.total_seconds()//60)}m ago"
        elif delta.days == 0:
            ts = f"{int(delta.total_seconds()//3600)}h ago"
        recent_activities.append({'type': 'club_added',
            'message': f"New club added: {club.name} — {club.location}",
            'time': ts, 'amount': None, 'sort_key': club.created_at.timestamp()})

    for sport in Sport.objects.select_related('club').order_by('-id')[:5]:
        recent_activities.append({'type': 'sport_added',
            'message': f"Sport added: {sport.name} at {sport.club.name} (₹{sport.price_per_hour}/hr)",
            'time': 'Recently', 'amount': None, 'sort_key': 0})

    recent_activities.sort(key=lambda x: x.get('sort_key', 0), reverse=True)
    for a in recent_activities:
        a.pop('sort_key', None)

    return Response({
        'total_bookings': total_bookings, 'confirmed_bookings': confirmed_bookings,
        'pending_bookings': pending_bookings, 'today_bookings': today_bookings,
        'active_users': active_users, 'total_revenue': float(total_earned),
        'total_refunded': float(total_refunded), 'net_revenue': round(net_revenue, 2),
        'weekly_bookings': weekly_bookings, 'recent_activities': recent_activities[:20],
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def monthly_report(request):
    from bookings.models import Booking
    from payments.models import Payment
    from clubs.models import Club
    from django.db.models import Sum
    from datetime import date
    from calendar import monthrange

    today = timezone.now().date()
    try:
        month = int(request.query_params.get('month', today.month))
        year = int(request.query_params.get('year', today.year))
    except ValueError:
        return Response({'error': 'month and year must be integers'}, status=status.HTTP_400_BAD_REQUEST)

    _, last_day = monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)

    month_bookings = Booking.objects.filter(
        date__gte=start_date, date__lte=end_date,
        status__in=['confirmed', 'refunded', 'cancelled']
    ).select_related('user', 'club', 'sport')

    club_breakdown = []
    for club in Club.objects.prefetch_related('sports'):
        cb = month_bookings.filter(club=club)
        if not cb.exists():
            continue
        revenue = Payment.objects.filter(booking__club=club, booking__date__gte=start_date,
            booking__date__lte=end_date, status='completed').aggregate(total=Sum('amount'))['total'] or 0
        refunds = Payment.objects.filter(booking__club=club, booking__date__gte=start_date,
            booking__date__lte=end_date, status='refunded').aggregate(total=Sum('amount'))['total'] or 0
        sports_data = []
        for s in club.sports.filter(is_active=True):
            sb = cb.filter(sport=s)
            if sb.exists():
                sr = Payment.objects.filter(booking__club=club, booking__sport=s,
                    booking__date__gte=start_date, booking__date__lte=end_date,
                    status='completed').aggregate(total=Sum('amount'))['total'] or 0
                sports_data.append({'name': s.name, 'bookings': sb.count(), 'revenue': float(sr)})
        club_breakdown.append({
            'club_name': club.name, 'location': club.location,
            'total_bookings': cb.count(), 'confirmed': cb.filter(status='confirmed').count(),
            'refunded': cb.filter(status='refunded').count(), 'cancelled': cb.filter(status='cancelled').count(),
            'gross_revenue': float(revenue), 'refunds': float(refunds),
            'net_revenue': float(revenue) - float(refunds), 'sports': sports_data
        })

    daily_data = []
    current = start_date
    while current <= end_date:
        db = month_bookings.filter(date=current)
        dr = Payment.objects.filter(booking__date=current, status='completed').aggregate(
            total=Sum('amount'))['total'] or 0
        daily_data.append({'date': str(current), 'day': current.strftime('%a %d'),
            'bookings': db.count(), 'confirmed': db.filter(status='confirmed').count(), 'revenue': float(dr)})
        current += timedelta(days=1)

    total_rev = Payment.objects.filter(booking__date__gte=start_date, booking__date__lte=end_date,
        status='completed').aggregate(total=Sum('amount'))['total'] or 0
    total_ref = Payment.objects.filter(booking__date__gte=start_date, booking__date__lte=end_date,
        status='refunded').aggregate(total=Sum('amount'))['total'] or 0

    return Response({
        'month': month, 'year': year, 'month_name': start_date.strftime('%B %Y'),
        'total_bookings': month_bookings.count(),
        'confirmed_bookings': month_bookings.filter(status='confirmed').count(),
        'cancelled_bookings': month_bookings.filter(status='cancelled').count(),
        'refunded_bookings': month_bookings.filter(status='refunded').count(),
        'gross_revenue': float(total_rev), 'total_refunds': float(total_ref),
        'net_revenue': float(total_rev) - float(total_ref),
        'club_breakdown': club_breakdown, 'daily_data': daily_data,
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def all_bookings(request):
    """Admin: list all bookings with payment method included (paginated)"""
    from bookings.models import Booking
    from payments.models import Payment

    bookings = Booking.objects.select_related(
        'user', 'club', 'sport', 'payment'
    ).order_by('-created_at')

    page_size = min(int(request.query_params.get('page_size', 50)), 200)
    page_number = int(request.query_params.get('page', 1))
    paginator = Paginator(bookings, page_size)
    page = paginator.get_page(page_number)

    payment_map = {
        p.booking_id: p.payment_method
        for p in Payment.objects.filter(booking__in=page.object_list).values_list(
            'booking_id', 'payment_method', named=True)
    }

    data = []
    for b in page.object_list:
        method = ''
        try:
            method = (b.payment.payment_method or '').strip()
        except Exception:
            pass
        if not method:
            method = (payment_map.get(b.id) or '').strip()
        if not method and b.status in ('confirmed', 'refunded'):
            method = 'card'

        data.append({
            'id': str(b.id),
            'user_name': b.user.get_full_name() or b.user.username,
            'club_name': b.club.name,
            'club_location': b.club.location,
            'sport_name': b.sport.name,
            'date': str(b.date),
            'start_time': str(b.start_time),
            'end_time': str(b.end_time),
            'amount': float(b.amount),
            'status': b.status,
            'payment_method': method or None,
            'created_at': b.created_at.isoformat(),
        })

    return Response({
        'count': paginator.count,
        'num_pages': paginator.num_pages,
        'page': page.number,
        'results': data,
    })


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_booking_status(request, booking_id):
    """Update booking status by admin"""
    from bookings.tasks import send_booking_status_update

    try:
        booking = Booking.objects.get(id=booking_id)
        new_status = request.data.get('status')

        if new_status not in ['pending', 'confirmed', 'cancelled', 'completed']:
            return Response(
                {'error': 'Invalid status. Must be: pending, confirmed, cancelled or completed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        old_status = booking.status
        booking.status = new_status
        booking.save()

        if old_status != new_status:
            send_booking_status_update.delay(booking.id, new_status)

        logger.info(f"Admin updated booking {booking_id} status: {old_status} -> {new_status}")

        return Response({
            'message': 'Status updated successfully',
            'booking_id': booking.id,
            'old_status': old_status,
            'new_status': new_status
        })

    except Booking.DoesNotExist:
        return Response(
            {'error': 'Booking not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def all_users(request):
    """Get all users for admin (paginated)"""
    users = User.objects.all().order_by('-date_joined')

    page_size = min(int(request.query_params.get('page_size', 50)), 200)
    page_number = int(request.query_params.get('page', 1))
    paginator = Paginator(users, page_size)
    page = paginator.get_page(page_number)

    data = [{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'first_name': u.first_name,
        'last_name': u.last_name,
        'full_name': u.get_full_name(),
        'mobile_number': u.mobile_number,
        'is_staff': u.is_staff,
        'is_active': u.is_active,
        'is_mobile_verified': u.is_mobile_verified,
        'date_joined': u.date_joined,
        'total_bookings': u.bookings.count()
    } for u in page.object_list]

    return Response({
        'count': paginator.count,
        'num_pages': paginator.num_pages,
        'page': page.number,
        'results': data,
    })


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def admin_clubs(request):
    """Admin: list all clubs or create a new one"""
    if request.method == 'GET':
        clubs = Club.objects.all()
        serializer = ClubSerializer(clubs, many=True)
        return Response(serializer.data)

    serializer = ClubSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
def admin_club_detail(request, club_id):
    """Admin: retrieve, update, or delete a specific club"""
    try:
        club = Club.objects.get(id=club_id)
    except Club.DoesNotExist:
        return Response({'error': 'Club not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ClubSerializer(club)
        return Response(serializer.data)

    if request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = ClubSerializer(club, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    club.delete()
    return Response({'message': 'Club deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


def _admin_login(request):
    """Admin login using mobile number + admin passcode or Django password."""

    mobile = request.data.get("mobile_number", "").strip()
    passcode = request.data.get("passcode", "").strip()
    password = request.data.get("password", "")

    if not mobile or not (passcode or password):
        return Response(
            {"error": "Mobile number and passcode/password required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    generic_error = {
        "error": "Invalid mobile number or passcode/password"
    }

    try:
        user = User.objects.get(
            mobile_number=mobile,
            is_staff=True,
            is_active=True,
        )
    except User.DoesNotExist:
        logger.warning(
            "Failed admin login attempt for mobile %s",
            mobile,
        )
        return Response(
            generic_error,
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if passcode:
        admin_passcode = getattr(settings, 'ADMIN_PASSCODE', '')
        if not admin_passcode or passcode != admin_passcode:
            logger.warning(
                "Failed admin login attempt for mobile %s",
                mobile,
            )
            return Response(
                generic_error,
                status=status.HTTP_401_UNAUTHORIZED,
            )
    else:
        if not user.check_password(password):
            logger.warning(
                "Failed admin login attempt for mobile %s",
                mobile,
            )
            return Response(
                generic_error,
                status=status.HTTP_401_UNAUTHORIZED,
            )

    refresh = RefreshToken.for_user(user)

    logger.info(
        "Admin %s logged in successfully",
        user.username,
    )

    return Response(
        {
            "message": "Admin login successful",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,
                "mobile_number": user.mobile_number,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
            },
        },
        status=status.HTTP_200_OK,
    )


# throttle_scope must be set on the plain function BEFORE api_view() wraps
# it into a view class — that's how ScopedRateThrottle picks it up for
# function-based views.
_admin_login.throttle_scope = 'auth'
admin_login = api_view(['POST'])(
    permission_classes([AllowAny])(
        throttle_classes([ScopedRateThrottle])(_admin_login)
    )
)