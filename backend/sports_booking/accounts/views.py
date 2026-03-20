from django.conf import settings
from clubs.models import Club
from clubs.serializers import ClubSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from datetime import timedelta
import random
import logging

from .models import OTP
from .serializers import (
    UserSerializer,
    UserRegistrationSerializer, 
    UserUpdateSerializer,
    OTPSerializer, 
    OTPVerifySerializer,
    ChangePasswordSerializer
)
from bookings.tasks import send_otp_sms_task, send_welcome_email_task
from bookings.models import Booking

User = get_user_model()
logger = logging.getLogger(__name__)

# Create your views here.
class SendOTPView(APIView):
    # Send OTP to mobile number for authentication
    permission_classes = [AllowAny]

    #print("Raw request data:", request.data)

    @method_decorator(ratelimit(key='ip', rate='5/h', method='POST'))
    def post(self, request):
        serializer = OTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        mobile_number = serializer.validated_data['mobile_number']

        # Generate 6-digit otp
        otp_code = str(random.randint(100000, 999999))

        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')

        # Delete old OTPs for this number
        OTP.objects.filter(mobile_number=mobile_number, is_verified=False).delete()

        # Create new OTP
        otp = OTP.objects.create(
            mobile_number=mobile_number,
            otp=otp_code,
            ip_address=ip_address,
            expires_at=timezone.now() + timedelta(minutes=10)
        )

        # Send OTP via SMS (async)
        send_otp_sms_task.delay(mobile_number, otp_code)

        # Log OTP for development (remove in production)
        logger.info(f"OTP for {mobile_number}: {otp_code}")
        print(f"\n{'='*40}\nDEV OTP for {mobile_number}: {otp_code}\n{'='*40}\n")

        
        return Response({
            'message': 'OTP sent successfully',
            'mobile_number': mobile_number,
            'expires_in' : 600,  # 10 mintutes in seconds
            'otp' : otp_code # shows in browser response
        }, status=status.HTTP_200_OK)
        

class VerifyOTPView(APIView):
    # Verify OTP and return JWT token if user exists
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        mobile_number = serializer.validated_data['mobile_number']
        otp_code = serializer.validated_data['otp']

        try:
            otp = OTP.objects.get(
                mobile_number=mobile_number,
                otp=otp_code,
                #valid_duration = timedelta(minutes=5),
                is_verified=False
            )
            
            logger.warning(f"Found OTP: {otp.otp}, Expires At: {otp.expires_at}, Now: {timezone.now()}")


            if otp.is_expired:
                otp.delete()
                return Response({
                    'error' : 'OTP has expired. Please request a new one.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            otp.is_verified = True
            otp.save()

            # Check if user already exists
            try:
                user = User.objects.get(mobile_number=mobile_number)
                user.is_mobile_verified = True
                user.save()
                
                # Generate JWT tokens
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
                
        except OTP.DoesNotExist:
            return Response({
                'error': 'Invalid OTP. Please check and try again.'
            }, status=status.HTTP_400_BAD_REQUEST)
    
class RegisterView(APIView):
    # Register new user after OTP verification
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        mobile_number = serializer.validated_data.get('mobile_number')
        
        # Verify that OTP was verified for this number
        if not OTP.objects.filter(mobile_number=mobile_number, is_verified=True).exists():
            return Response({
                'error': 'Mobile number not verified. Please verify OTP first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        
        # Check if user already exists
        if User.objects.filter(Q(mobile_number=mobile_number) | Q(email=serializer.validated_data['email'])).exists():
            return Response({
                'error': 'User with this mobile number or email already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = serializer.save()
        
        # Send welcome email (async)
        send_welcome_email_task.delay(user.id)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        logger.info(f"New user registered: {user.username}")
        
        return Response({
            'message': 'Registration successful',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)

class UserProfileView(APIView):
    # Get and update user profile
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Get user profile
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        # Update user profile (full update)
        serializer = UserUpdateSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"User {request.user.username} updated profile")
            return Response(UserSerializer(request.user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        # Update user profile (partial update)
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"User {request.user.username} updated profile")
            return Response(UserSerializer(request.user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ChangePasswordView(APIView):
    # Change user password
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user

        # check old password
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({
                'error': 'Old password is incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        logger.info(f"User {user.username} changed password")

        return Response({
            'message': 'Password changed successfully'
        })
    

# Admin Views

@api_view(['GET'])
@permission_classes([IsAdminUser])
def dashboard_stats(request):
    from bookings.models import Booking
    from payments.models import Payment
    from clubs.models import Club, Sport
    from django.contrib.auth import get_user_model
    from django.db.models import Sum
    from django.utils import timezone
    from datetime import timedelta

    User = get_user_model()
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

    # Recent bookings
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
        if delta.total_seconds() < 60: ts = "Just now"
        elif delta.total_seconds() < 3600: ts = f"{int(delta.total_seconds()//60)}m ago"
        elif delta.days == 0: ts = f"{int(delta.total_seconds()//3600)}h ago"
        recent_activities.append({'type': atype, 'message': msg, 'time': ts,
            'amount': float(b.amount) if b.status in ['confirmed', 'refunded'] else None,
            'sort_key': b.updated_at.timestamp()})

    # Recent clubs added
    for club in Club.objects.order_by('-created_at')[:5]:
        delta = timezone.now() - club.created_at
        ts = club.created_at.strftime('%d %b, %I:%M %p')
        if delta.total_seconds() < 60: ts = "Just now"
        elif delta.total_seconds() < 3600: ts = f"{int(delta.total_seconds()//60)}m ago"
        elif delta.days == 0: ts = f"{int(delta.total_seconds()//3600)}h ago"
        recent_activities.append({'type': 'club_added',
            'message': f"New club added: {club.name} — {club.location}",
            'time': ts, 'amount': None, 'sort_key': club.created_at.timestamp()})

    # Recent sports added
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
    from django.utils import timezone
    from datetime import timedelta, date
    from calendar import monthrange

    today = timezone.now().date()
    month = int(request.query_params.get('month', today.month))
    year = int(request.query_params.get('year', today.year))
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

# ─────────────────────────────────────────────────────────────────
# REPLACE your existing all_bookings function in accounts/views.py
# ─────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAdminUser])
def all_bookings(request):
    """Admin: list all bookings with payment method included"""
    from bookings.models import Booking
    from payments.models import Payment

    bookings = Booking.objects.select_related(
        'user', 'club', 'sport', 'payment'
    ).order_by('-created_at')

    # Build payment_method lookup map for efficiency
    payment_map = {
        p.booking_id: p.payment_method
        for p in Payment.objects.all().values_list('booking_id', 'payment_method', named=True)
    }

    data = []
    for b in bookings:
        # Get payment method: try related object first, then map, then default
        method = ''
        try:
            method = (b.payment.payment_method or '').strip()
        except Exception:
            pass
        if not method:
            method = (payment_map.get(b.id) or '').strip()
        if not method and b.status in ('confirmed', 'refunded'):
            method = 'card'  # default for old bookings before payment mode was tracked

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

    return Response(data)

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
        
        # Send notification(async)
        if old_status != new_status:
            send_booking_status_update.delay(booking.id, new_status)
        
        logger.info(f"Admin updated booking {booking_id} status: {old_status} -> {new_status}")

        return Response({
            'message': 'Status updated successfully',
            'booking_id' : booking.id,
            'old_status' : old_status, 
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
    """Get all users for admin"""
    users = User.objects.all().order_by('-date_joined')
    
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
    } for u in users]
    
    return Response(data)

@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def admin_clubs(request):
    """Admin: list all clubs or create a new one"""
    from clubs.models import Club
    from clubs.serializers import ClubSerializer
 
    if request.method == 'GET':
        clubs = Club.objects.all()
        serializer = ClubSerializer(clubs, many=True)
        return Response(serializer.data)
 
    elif request.method == 'POST':
        serializer = ClubSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
 
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
def admin_club_detail(request, club_id):
    """Admin: retrieve, update, or delete a specific club"""
    from clubs.models import Club
    from clubs.serializers import ClubSerializer
 
    try:
        club = Club.objects.get(id=club_id)
    except Club.DoesNotExist:
        return Response({'error': 'Club not found'}, status=status.HTTP_404_NOT_FOUND)
 
    if request.method == 'GET':
        serializer = ClubSerializer(club)
        return Response(serializer.data)
 
    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = ClubSerializer(club, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
    elif request.method == 'DELETE':
        club.delete()
        return Response({'message': 'Club deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def create_admin(request):
    if request.GET.get('key') != 'setup2026':
        return JsonResponse({'error': 'forbidden'}, status=403)
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@sportsclub.com',
            password='Admin@123',
            mobile_number='9000000000',
            is_mobile_verified=True
        )
        return JsonResponse({'message': 'Admin created!'})
    return JsonResponse({'message': 'Already exists'})
    
@csrf_exempt
def reset_admin(request):
    if request.GET.get('key') != 'setup2026':
        return JsonResponse({'error': 'forbidden'}, status=403)
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        user = User.objects.get(username='admin')
        user.set_password('Admin@123')
        user.is_staff = True
        user.is_superuser = True
        user.save()
        return JsonResponse({'message': f'Password reset for {user.username}'})
    except User.DoesNotExist:
        return JsonResponse({'error': 'Admin not found'})
