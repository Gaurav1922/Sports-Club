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
        
        return Response({
            'message': 'OTP sent successfully',
            'mobile_number': mobile_number,
            'expires_in' : 600  # 10 mintutes in seconds
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
    """Get dashboard statistics for admin"""
    today = timezone.now().date()
    
    total_revenue = Booking.objects.filter(
        status='confirmed'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    revenue_this_month = Booking.objects.filter(
        status='confirmed',
        created_at__month=today.month,
        created_at__year=today.year
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    stats = {
        'total_bookings': Booking.objects.count(),
        'total_revenue': float(total_revenue),
        'active_users': User.objects.filter(
            is_active=True,
            bookings__isnull=False
        ).distinct().count(),
        'today_bookings': Booking.objects.filter(date=today).count(),
        'pending_bookings': Booking.objects.filter(status='pending').count(),
        'confirmed_bookings': Booking.objects.filter(status='confirmed').count(),
        'completed_bookings': Booking.objects.filter(status='completed').count(),
        'cancelled_bookings': Booking.objects.filter(status='cancelled').count(),
        'revenue_this_month': float(revenue_this_month),
        'total_users': User.objects.count(),
        'new_users_this_month': User.objects.filter(
            date_joined__month=today.month,
            date_joined__year=today.year
        ).count(),
        'verified_users': User.objects.filter(is_mobile_verified=True).count()
    }
    
    return Response(stats)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def all_bookings(request):
    """Get all bookings for admin"""
    bookings = Booking.objects.select_related('user', 'club', 'sport').all()
    
    data = [{
        'id': b.id,
        'user_name': b.user.get_full_name() or b.user.username,
        'user_email': b.user.email,
        'user_mobile': b.user.mobile_number,
        'club_name': b.club.name,
        'sport_name': b.sport.name,
        'date': b.date,
        'start_time': b.start_time,
        'end_time': b.end_time,
        'amount': float(b.amount),
        'status': b.status,
        'created_at': b.created_at
    } for b in bookings]
    
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