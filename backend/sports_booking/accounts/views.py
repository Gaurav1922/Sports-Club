from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from django.core.cache import cache
from .models import OTP
from .serializers import SendOTPSerializer, VerifyOTPSerializer, UserSerializer
from .tasks import send_otp_sms
import logging
from django.conf import settings

logger = logging.getLogger(__name__)
User = get_user_model()

# Create your views here.
class SendOTPView(APIView):
    permission_classes = []
    throttle_scope = 'otp'

    #print("Raw request data:", request.data)


    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']

            # check rate limiting
            cache_key = f"otp_requests_{phone_number}"
            request_count = cache.get(cache_key, 0)

            if request_count >= 10: # Max 3 otps per hour
                return Response({
                    'error': 'Too many OTP requests, Please try again later.'
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Delete old OTPs
            OTP.objects.filter(phone_number=phone_number).delete()

            # Create new OTP
            otp_obj = OTP.objects.create(phone_number=phone_number)

            # Send OTP via SMS (async)
            send_otp_sms.delay(phone_number, otp_obj.otp)

            # Update rate limiting
            cache.set(cache_key, request_count + 1, timeout=3600)   # 1 hour

            logger.info(f"OTP sent to {phone_number}")

            response_data = {'message': 'OTP sent successfully'}

            # Include OTP in development mode only
            if hasattr(settings, 'DEBUG') and settings.DEBUG:
                response_data['otp'] = otp_obj.otp

            return Response(response_data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
        return Response({
                'message': 'OTP sent successfully',
                'otp': otp_obj.otp # Remove this in production
            }, status=status.HTTP_200_OK)
        

class VerifyOTPView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            otp = serializer.validated_data['otp']

            try:
                otp_obj = OTP.objects.get(
                    phone_number=phone_number,
                    otp=otp,
                    is_verified=False
                )

                if not otp_obj.is_valid():
                    return Response({
                        'error': 'OTP has expired'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                if not otp_obj.increment_attempts():
                    return Response({
                        'error': 'Too many invalid attempts'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Mark OTP as verified
                otp_obj.is_verified=True
                otp_obj.save()

                # Get or Create user
                user, created = User.objects.get_or_create(
                    phone_number=phone_number,
                    defaults={
                        'username': str(phone_number), 'is_phone_verified': True
                    }
                )

                if not created:
                    user.is_phone_verified = True
                    user.reset_failed_attempts()
                    user.save()
                
                # Generate Token
                token, _ = Token.objects.get_or_create(user=user)

                logger.info(f"User {phone_number} verified successfully")


                return Response({
                    'token': token.key,
                    'user': UserSerializer(user).data
                }, status=status.HTTP_200_OK)
            
            except OTP.DoesNotExist:
                return Response({
                    'error': 'Invalid OTP'
                }, status=status.HTTP_400_BAD_REQUEST)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserProfileView(APIView):
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def put(self,request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    