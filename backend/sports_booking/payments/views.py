from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import HttpResponse
from django.db import transaction
from .models import Payment
from .serializers import PaymentSerializer, CreatePaymentSerializer
from bookings.models import Booking
import logging
import stripe 
from stripe import StripeError
from django.conf import settings
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY  # ✅ critical line

# Initialize Stripe API key
def get_stripe_key():
    """Get and set Stripe API key safely"""
    api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
    if not api_key:
        logger.error("STRIPE_SECRET_KEY not found in settings")
        raise ValueError("Stripe API key not configured")
    return api_key

# Set Stripe API key
try:
    stripe.api_key = get_stripe_key()
    logger.info("Stripe API key initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Stripe API key: {e}")


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Payment.objects.filter(
            booking__user=self.request.user,
            is_locked=False  # Don't show locked payments to users
        ).select_related('booking', 'booking__club', 'booking__time_slot')
    
    def create(self, request):
        """Create a new secure payment"""
        serializer = CreatePaymentSerializer(data=request.data)
        if serializer.is_valid():
            booking_id = serializer.validated_data['booking'].id
            booking = get_object_or_404(Booking, id=booking_id, user=request.user)
            
            # Check if payment already exists
            if hasattr(booking, 'payment'):
                existing_payment = booking.payment
                
                # If expired, allow new payment creation
                if not existing_payment.is_expired():
                    return Response({
                        'error': 'Active payment already exists for this booking',
                        'payment_id': existing_payment.id,
                        'expires_at': existing_payment.expires_at
                    }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    # Mark expired payment as expired
                    existing_payment.status = 'expired'
                    existing_payment.save()
                    
            # Log payment creation
            payment = serializer.save()
            logger.info(f"Secure payment created: {payment.transaction_id} for user {request.user.id}")
            
            response_serializer = PaymentSerializer(payment)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def secure_qr(self, request, pk=None):
        """Get secure QR code with integrity verification"""
        payment = self.get_object()
        
        # Security checks
        can_process, error_msg = payment.can_process_payment()
        if not can_process:
            # Increment attempts for suspicious activity
            if "integrity" in error_msg.lower():
                payment.increment_attempts()
            
            return Response({
                'error': error_msg,
                'locked': payment.is_locked
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Additional security: Check if QR code exists and is valid
        if not payment.qr_code:
            return Response({
                'error': 'QR code not available'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verify integrity
        if not payment.verify_qr_integrity():
            payment.increment_attempts()
            logger.warning(f"QR integrity check failed for payment {payment.transaction_id}")
            
            return Response({
                'error': 'QR code integrity verification failed'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            with open(payment.qr_code.path, 'rb') as qr_file:
                response = HttpResponse(qr_file.read(), content_type='image/png')
                response['Content-Disposition'] = f'inline; filename="secure_qr_{payment.transaction_id}.png"'
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                response['X-Content-Type-Options'] = 'nosniff'
                response['X-Frame-Options'] = 'DENY'
                return response
                
        except FileNotFoundError:
            logger.error(f"QR code file not found for payment {payment.transaction_id}")
            return Response({
                'error': 'QR code file not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def verify_payment(self, request, pk=None):
        """Verify and confirm payment with security checks"""
        payment = self.get_object()
        
        # Security validation
        can_process, error_msg = payment.can_process_payment()
        if not can_process:
            return Response({
                'error': error_msg
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get verification data from request
        verification_data = request.data
        provided_token = verification_data.get('security_token')
        
        # Verify security token (if implementing additional security)
        if provided_token and provided_token != payment.security_token:
            payment.increment_attempts()
            return Response({
                'error': 'Security token verification failed'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Simulate payment gateway verification
        payment_verified = verification_data.get('payment_verified', True)
        
        if payment_verified:
            with transaction.atomic():
                # Mark payment as completed
                payment.status = 'completed'
                payment.completed_at = timezone.now()
                payment.save()
            
                # Update booking status
                booking = payment.booking
                booking.payment_status = 'completed'
                booking.status = 'confirmed'
                booking.save()
            
                # Update time slot availability
                time_slot = booking.time_slot
                time_slot.current_bookings += 1
                if time_slot.current_bookings >= time_slot.max_capacity:
                    time_slot.is_available = False
                time_slot.save()
            
                logger.info(f"Payment confirmed: {payment.transaction_id}")
            
                # Send confirmation email (async) - uncomment if you have celery setup
                # from .tasks import send_payment_confirmation_email
                # send_payment_confirmation_email.delay(payment.id)
            
                return Response({
                    'message': 'Payment verified and confirmed successfully',
                    'payment': PaymentSerializer(payment).data
                }, status=status.HTTP_200_OK)
        
        else:
            payment.increment_attempts()
            return Response({
                'error': 'Payment verification failed'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def regenerate_qr(self, request, pk=None):
        """Regenerate QR code (expired payments only)"""
        payment = self.get_object()
        
        if not payment.is_expired():
            return Response({
                'error': 'Can only regenerate QR for expired payments'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if payment.is_locked:
            return Response({
                'error': 'Payment is locked due to security violations'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Reset payment status and attempts
        payment.status = 'pending'
        payment.attempts = 0
        payment.last_attempt_at = None
        
        # Generate new QR code
        qr_generated = payment.generate_qr_code(force_regenerate=True)
        if qr_generated:
            payment.save()
            return Response({
                'message': 'New QR code generated successfully',
                'expires_at': payment.expires_at
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Failed to generate new QR code'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def payment_status(self, request):
        """Check payment status with security validation"""
        transaction_id = request.query_params.get('transaction_id')
        
        if not transaction_id:
            return Response({
                'error': 'transaction_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            payment = Payment.objects.get(
                transaction_id=transaction_id,
                booking__user=request.user
            )
            
            # Return status with security info
            return Response({
                'transaction_id': payment.transaction_id,
                'status': payment.status,
                'expires_at': payment.expires_at,
                'is_expired': payment.is_expired(),
                'is_locked': payment.is_locked,
                'attempts_remaining': max(0, 5 - payment.attempts)          
            })
            
        except Payment.DoesNotExist:
            return Response({
                'error': 'Payment not found'
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def create_payment_intent(self, request):
        """Create Stripe Payment Intent"""
        booking_id = request.data.get('booking')

        if not booking_id:
            return Response({
                'error': 'Booking ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Ensure Stripe API key is set
        if not stripe.api_key:
            try:
                stripe.api_key = get_stripe_key()
            except Exception as e:
                logger.error(f"Stripe API key not configured: {e}")
                return Response({
                    'error': 'Payment system not configured. Please contact support.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            booking = get_object_or_404(Booking, id=booking_id, user=request.user)

            # Check if payment already exists
            if hasattr(booking, 'payment'):
                existing_payment = booking.payment
                if existing_payment.status == 'pending' and existing_payment.stripe_client_secret:
                    # Return existing payment intent
                    return Response({
                        'payment_id': str(existing_payment.id),
                        'payment_intent_id': existing_payment.stripe_payment_intent_id,
                        'client_secret': existing_payment.stripe_client_secret,
                        'amount': str(existing_payment.amount),
                        'currency': 'inr',
                        'status': existing_payment.status,
                        'publishable_key': settings.STRIPE_PUBLIC_KEY
                    }, status=status.HTTP_200_OK)

            # Create or get payment - FIX: get_or_create returns (object, created) tuple
            payment, created = Payment.objects.get_or_create(
                booking=booking,
                defaults={
                    'amount': booking.total_amount,
                    'payment_method': 'stripe_card',
                    'status': 'pending'
                }
            )

            # If payment already exists but doesn't have stripe data, update it
            if not created and not payment.stripe_client_secret:
                payment.amount = booking.total_amount
                payment.payment_method = 'stripe_card'
                payment.status = 'pending'
                payment.save()

            # Create Payment Intent
            intent = stripe.PaymentIntent.create(
                amount=int(payment.amount * 100),  # Stripe uses cents
                currency='inr',
                automatic_payment_methods={
                    "enabled": True,
                    "allow_redirects": "never"
                },
                metadata={
                    'booking_id': str(booking_id),
                    'payment_id': str(payment.id),
                    'user_id': str(request.user.id)
                }
            )

            # Update payment with Stripe data
            payment.stripe_payment_intent_id = intent.id
            payment.stripe_client_secret = intent.client_secret
            payment.save()

            logger.info(f"Payment intent created: {intent.id} for booking {booking.id}")
            
            # Get publishable key safely
            publishable_key = getattr(settings, 'STRIPE_PUBLIC_KEY', None)
            
            response_data = {
                'payment_id': str(payment.id),
                'payment_intent_id': intent.id,
                'client_secret': intent.client_secret,
                'amount': str(payment.amount),
                'currency': 'inr',
                'status': payment.status
            }
            
            # Only include publishable key if it exists
            if publishable_key:
                response_data['publishable_key'] = publishable_key
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        except StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return Response({
                'error': f'Stripe error: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
        except Exception as e:
            logger.error(f"Payment intent creation failed: {str(e)}")
            return Response({
                'error': f'Payment creation failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    #from stripe.error import StripeError

    @action(detail=True, methods=['post'])
    def confirm_payment(self, request, pk=None):
        """Confirm Stripe payment"""
        payment = self.get_object()
        payment_intent_id = request.data.get('payment_intent_id')

        try:
            # ✅ Confirm and attach a test card method directly
            intent = stripe.PaymentIntent.confirm(
                payment_intent_id,
                payment_method='pm_card_visa'  # Test payment method
            )

            if intent.status == 'succeeded':
                payment.status = 'completed'
                payment.completed_at = timezone.now()
                payment.save()

                booking = payment.booking
                booking.payment_status = 'completed'
                booking.status = 'confirmed'
                booking.save()

                return Response({
                    "message": "Payment confirmed successfully",
                    "payment_status": payment.status,
                    "stripe_status": intent.status
                })

            return Response({
                "error": "Payment not successful",
                "stripe_status": intent.status
            }, status=status.HTTP_400_BAD_REQUEST)

        except StripeError as e:
            return Response({
                "error": f"Stripe error: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not payment_intent_id:
            return Response({
                'error': "Payment Intent ID is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Retrieve payment intent from Stripe
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            if intent.status == 'succeeded':
                with transaction.atomic():
                    # Update payment status
                    payment.status = 'completed'
                    payment.completed_at = timezone.now()

                    # Extract card details if available
                    if intent.charges.data:
                        charge = intent.charges.data[0]
                        if hasattr(charge, 'payment_method_details') and charge.payment_method_details.card:
                            payment.card_last_four = charge.payment_method_details.card.last4
                            payment.card_brand = charge.payment_method_details.card.brand
                    
                    payment.save()

                    # Update booking status
                    booking = payment.booking
                    booking.payment_status = 'completed'
                    booking.status = 'confirmed'
                    booking.save()

                    # Update time slot
                    time_slot = booking.time_slot
                    time_slot.current_bookings += 1
                    if time_slot.current_bookings >= time_slot.max_capacity:
                        time_slot.is_available = False
                    time_slot.save()

                logger.info(f"Payment confirmed: {payment_intent_id}")
                
                return Response({
                    'message': 'Payment confirmed successfully',
                    'payment_status': payment.status,
                    'booking_status': booking.status
                }, status=status.HTTP_200_OK)
            
            else:
                payment.status = 'failed'
                payment.save()

                return Response({
                    'error': 'Payment not successful',
                    'stripe_status': intent.status
                }, status=status.HTTP_400_BAD_REQUEST)

        except StripeError as e:
            logger.error(f"Stripe error during confirmation: {str(e)}")
            return Response({
                'error': f'Stripe error: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Payment confirmation failed: {str(e)}")
            return Response({
                'error': f'Confirmation failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=['post'])
    def webhook(self, request):
        """Handle Stripe Webhooks"""
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            logger.error("Invalid webhook payload")
            return Response({
                'error': 'Invalid payload'
            }, status=status.HTTP_400_BAD_REQUEST)
        except StripeError:
            logger.error("Invalid webhook signature")
            return Response({
                'error': 'Invalid signature'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Handle the event
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']

            try:
                payment = Payment.objects.get(
                    stripe_payment_intent_id=payment_intent['id']
                )
                
                with transaction.atomic():
                    payment.status = 'completed'
                    payment.completed_at = timezone.now()
                    payment.save()

                    # Update booking
                    booking = payment.booking
                    booking.payment_status = 'completed'
                    booking.status = 'confirmed'
                    booking.save()

                    # Update time slot
                    time_slot = booking.time_slot
                    time_slot.current_bookings += 1
                    if time_slot.current_bookings >= time_slot.max_capacity:
                        time_slot.is_available = False
                    time_slot.save()

                logger.info(f"Webhook processed: payment {payment.id} completed")

            except Payment.DoesNotExist:
                logger.warning(f"Payment not found for intent {payment_intent['id']}")
        
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            
            try:
                payment = Payment.objects.get(
                    stripe_payment_intent_id=payment_intent['id']
                )
                payment.status = 'failed'
                payment.save()
                
                logger.info(f"Webhook processed: payment {payment.id} failed")
            except Payment.DoesNotExist:
                logger.warning(f"Payment not found for failed intent {payment_intent['id']}")
        
        return Response({'status': 'success'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def cancel_payment(self, request, pk=None):
        """Cancel a pending payment"""
        payment = self.get_object()

        if payment.status != 'pending':
            return Response({
                'error': f'Cannot cancel payment with status: {payment.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        payment.status = 'failed'
        payment.save()

        # Update booking status
        booking = payment.booking
        booking.payment_status = 'failed'
        booking.status = 'cancelled'
        booking.save()

        return Response({
            'message': 'Payment cancelled successfully'   
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def qr_code(self, request, pk=None):
        """Get QR code image for payment"""
        payment = self.get_object()

        if not payment.qr_code:
            return Response({
                'error': 'QR code not available for this payment'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            with open(payment.qr_code.path, 'rb') as qr_file:
                response = HttpResponse(qr_file.read(), content_type='image/png')
                response['Content-Disposition'] = f'inline; filename="qr_{payment.transaction_id}.png"'
                return response
        except FileNotFoundError:
            return Response({
                'error': 'QR code file not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def request_refund(self, request, pk=None):
        """Request refund for a completed payment"""
        payment = self.get_object()

        if payment.status != 'completed':
            return Response({
                'error': 'Can only refund completed payments'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if booking can be cancelled
        booking = payment.booking
        time_slot = booking.time_slot

        from datetime import datetime, timedelta
        slot_datetime = datetime.combine(time_slot.date, time_slot.start_time)
        current_time = datetime.now()

        if slot_datetime - current_time < timedelta(hours=24):
            return Response({
                'error': 'Cannot refund booking less than 24 hours before slot time'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Process refund
        with transaction.atomic():
            payment.status = 'refunded'
            payment.save()

            # Update booking
            booking.payment_status = 'refunded'
            booking.status = 'cancelled'
            booking.save()

            # Free up the time slot
            time_slot.current_bookings = max(0, time_slot.current_bookings - 1)
            time_slot.is_available = True
            time_slot.save()

        return Response({
            'message': 'Refund processed successfully',
            'refund_amount': payment.amount
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def payment_methods(self, request):
        """Get available payment methods"""
        methods = [
            {
                'id': 'stripe_card',
                'name': 'Credit/Debit Card',
                'description': 'Pay securely using your card via Stripe',
                'icon': 'credit-card',
                'enabled': True
            },
            {
                'id': 'qr',
                'name': 'QR Code / UPI',
                'description': 'Pay using any UPI app by scanning QR code',
                'icon': 'qr-code',
                'enabled': True
            },
            {
                'id': 'upi',
                'name': 'UPI Direct',
                'description': 'Pay directly using UPI ID',
                'icon': 'smartphone',
                'enabled': False
            },
            {
                'id': 'wallet',
                'name': 'Digital Wallet',
                'description': 'Paytm, PhonePe, Google Pay (Coming Soon)',
                'icon': 'wallet',
                'enabled': False
            }
        ]
        
        return Response(methods, status=status.HTTP_200_OK)


# Admin-only views for payment management
class AdminPaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=True, methods=['post'])
    def force_regenerate_qr(self, request, pk=None):
        """Admin: Force regenerate QR code"""
        payment = self.get_object()
        
        # Only admins can force regenerate
        qr_generated = payment.generate_qr_code(
            force_regenerate=True, 
            admin_user=request.user.username
        )
        
        if qr_generated:
            logger.warning(f"Admin {request.user.username} force-regenerated QR for payment {payment.transaction_id}")
            return Response({
                'message': 'QR code force-regenerated by admin',
                'expires_at': payment.expires_at
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Failed to regenerate QR code'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def unlock_payment(self, request, pk=None):
        """Admin: Unlock payment after security violation"""
        payment = self.get_object()
        
        if not payment.is_locked:
            return Response({
                'error': 'Payment is not locked'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Reset security flags
        payment.is_locked = False
        payment.attempts = 0
        payment.status = 'pending'
        payment.admin_notes = (payment.admin_notes or '') + f"\nUnlocked by admin {request.user.username} at {timezone.now()}"
        payment.save()
        
        logger.warning(f"Admin {request.user.username} unlocked payment {payment.transaction_id}")
        
        return Response({
            'message': 'Payment unlocked successfully'
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def security_report(self, request):
        """Admin: Get security violations report"""
        locked_payments = Payment.objects.filter(is_locked=True)
        high_attempts = Payment.objects.filter(attempts__gte=3, is_locked=False)
        
        return Response({
            'locked_payments': locked_payments.count(),
            'high_attempt_payments': high_attempts.count(),
            'total_violations': locked_payments.count() + high_attempts.count(),
            'recent_violations': PaymentSerializer(
                locked_payments.order_by('-last_attempt_at')[:10], 
                many=True
            ).data
        }, status=status.HTTP_200_OK)