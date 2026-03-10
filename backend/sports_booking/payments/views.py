import stripe
from django.conf import settings
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from bookings.models import Booking, SlotLock
from .models import Payment
from .serializers import (
    PaymentSerializer, 
    PaymentIntentSerializer, 
    PaymentConfirmSerializer
)
from bookings.tasks import (
    send_booking_confirmation_email, 
    send_booking_confirmation_sms
)
from django.db import transaction
import logging

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing payment history"""
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Payment.objects.all().select_related('booking', 'booking__club', 'booking__sport')
        return Payment.objects.filter(
            booking__user=self.request.user
        ).select_related('booking', 'booking__club', 'booking__sport')
        
        
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment_intent(request):
    """Create Stripe payment intent for booking"""
    serializer = PaymentIntentSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        booking_id = serializer.validated_data['booking_id']
        booking = Booking.objects.select_related('club', 'sport').get(
            id=booking_id,
            user=request.user
        )
        
        if booking.status != 'pending':
            return Response(
                {'error': 'Booking is not in pending state'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if payment already exists
        if hasattr(booking, 'payment'):
            if booking.payment.status == 'completed':
                return Response(
                    {'error': 'Payment already exists for this booking'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif booking.payment.status == 'pending':
                # Return existing payment intent
                intent = stripe.PaymentIntent.retrieve(booking.payment.stripe_payment_intent_id)
                return Response({
                    'client_secret': intent.client_secret,
                    'payment_intent_id': intent.id,
                    'amount': float(booking.amount)
                }, status=status.HTTP_200_OK)
        
        # Create Stripe payment intent
        intent = stripe.PaymentIntent.create(
            amount=int(booking.amount * 100),  # Convert to paise/cents
            currency='inr',
            metadata={
                'booking_id': booking.id,
                'user_id': request.user.id,
                'club_name': booking.club.name,
                'sport_name': booking.sport.name,
                'date': str(booking.date),
                'time': f"{booking.start_time} - {booking.end_time}"
            },
            description=f"Booking at {booking.club.name} for {booking.sport.name}",
            # automatic_payment_methods={'enabled': True}
        )
        
        # Create payment record
        payment = Payment.objects.create(
            booking=booking,
            stripe_payment_intent_id=intent.id,
            amount=booking.amount,
            currency='INR',
            status='pending',
            metadata={
                'stripe_intent_status': intent.status,
                'created_via': 'api'
            }
        )
        
        logger.info(f"Payment intent created: {intent.id} for booking {booking.id}")
        
        return Response({
            'client_secret': intent.client_secret,
            'payment_intent_id': intent.id,
            'amount': float(booking.amount),
            'currency': 'INR'
        }, status=status.HTTP_200_OK)
        
    except Booking.DoesNotExist:
        return Response(
            {'error': 'Booking not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        return Response(
            {'error': f'Payment processing error: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error creating payment intent: {str(e)}")
        return Response(
            {'error': 'An unexcepted error occured'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_payment(request):
    """Confirm payment and update booking status"""
    serializer = PaymentConfirmSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        booking_id = serializer.validated_data['booking_id']
        payment_intent_id = serializer.validated_data['payment_intent_id']
        
        booking = Booking.objects.select_related('lock', 'club', 'sport').get(
            id=booking_id,
            user=request.user
        )
        
        # Verify payment with Stripe
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        if intent.status == 'succeeded':
            with transaction.atomic():
                # Update or create payment record
                payment, created = Payment.objects.get_or_create(
                    booking=booking,
                    stripe_payment_intent_id=payment_intent_id,
                    defaults={
                        'amount': booking.amount,
                        'currency': 'INR',
                        'status': 'completed',
                        'completed_at': timezone.now()
                    }
                )
                
                if not created:
                    payment.status = 'completed'
                    payment.completed_at = timezone.now()
                
                # Extract payment method from charges
                if intent.charges.data:
                    charge = intent.charges.data[0]
                    payment.payment_method = charge.payment_method_details.type 
                    payment.metadata ={
                        'stripe_intent_status': intent.status,
                        'charge_id': charge.id,
                        'receipt_url': charge.receipt_url
                    }
                    
                payment.save()
                
                # Update booking status
                booking.status = 'confirmed'
                booking.save()
                
                # Mark lock as converted
                if booking.lock:
                    booking.lock.is_converted = True
                    booking.lock.save()
                
                # Send notifications asynchronously
                send_booking_confirmation_email.delay(booking.id)
                send_booking_confirmation_sms.delay(booking.id)
                
            logger.info(f"Payment confirmed for booking {booking.id}")
            
            return Response({
                'message': 'Payment successful',
                'booking_id': booking.id,
                'payment_id': payment.id,
                'status': 'confirmed',
                'receipt_url': payment.metadata.get('receipt_url') if payment.metadata else None
            }, status=status.HTTP_200_OK)
        elif intent.status == 'requires_payment_method':
            return Response(
                {'error': 'Payment failed. Please try again with a different payment method.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            return Response(
                {'error': f'Payment Status: {intent.status}. Please try again.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Booking.DoesNotExist:
        return Response(
            {'error': 'Booking not found'},
            status=status.HTTP_404_NOT_FOUND
        )
        
    except stripe.error.StripeError as e:
        logger .error(f"Stripe error during confirmation: {str(e)}")
        return Response(
            {'error': f'Payment verification failed: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error confirming payment: {str(e)}")
        return Response(
            {'error': 'An unexpected error occurred'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        

@api_view(['POST'])
@permission_classes([AllowAny])
def stripe_webhook(request):
    """Handle Stripe webhooks"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        
        logger.info(f"Webhook event received: {event['type']}")
        
        # Handle payment_intent.succeeded event
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            booking_id = payment_intent['metadata'].get('booking_id')
            
            if booking_id:
                with transaction.atomic():
                    booking = Booking.objects.select_related('lock').get(id=booking_id)
                    
                    # Update or create payment status
                    payment, created = Payment.objects.get_or_create(
                        booking=booking,
                        stripe_payment_intent_id=payment_intent['id'],
                        defaults={
                            'amount': booking.amount,
                            'currency': 'INR',
                            'status': 'completed',
                            'completed_at': timezone.now()
                        }
                    )
                    
                    if not created and payment.status != 'completed':
                        payment.status = 'completed'
                        payment.completed_at = timezone.now()
                        payment.save()
                    # Update booking status
                    if booking.status != 'confirmed':
                        booking.status = 'confirmed'
                        booking.save()
                        
                        # Mark lock as converted
                        if booking.lock:
                            booking.lock.is_converted = True
                            booking.lock.save()
                    
                        # Send notifications
                        send_booking_confirmation_email.delay(booking.id)
                        send_booking_confirmation_sms.delay(booking.id)
                
                logger.info(f"Webhook: Payment succeeded for booking {booking_id}")
        
        # Handle payment_intent.payment_failed event
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            booking_id = payment_intent['metadata'].get('booking_id')
            
            if booking_id:
                try:
                    
                    payment = Payment.objects.get(
                        stripe_payment_intent_id=payment_intent['id']
                    )
                    payment.status = 'failed'
                    payment.metadata = {
                        'error': payment_intent.get('last_payment_error', {}).get('message', 'Unknown error')
                    }
                    payment.save()
                    logger.warning(f"Webhook: Payment failed for booking {booking_id}")
                except Payment.DoesNotExist:
                    logger.warning(f"Webhook: Payment record not found for intent {payment_intent['id']}")
        
        return Response({'status': 'success'}, status=status.HTTP_200_OK)
        
    except ValueError as e:
        logger.error(f"Webhook error: Invalid payload - {str(e)}")
        return Response(
            {'error': 'Invalid payload'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Webhook error: Invalid signature - {str(e)}")
        return Response(
            {'error': 'Invalid signature'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
@permission_classes([IsAdminUser])
def refund_payment(request, payment_id):
    """Refund a payment (admin only)"""
    try:
        payment = Payment.objects.get(id=payment_id)
        
        if payment.status != 'completed':
            return Response(
                {'error': 'Can only refund completed payments'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create refund in Stripe
        refund = stripe.Refund.create(
            payment_intent=payment.stripe_payment_intent_id
        )
        
        # Update payment status
        payment.status = 'refunded'
        payment.metadata = payment.metadata or {}
        payment.metadata['refund_id'] = refund.id
        payment.metadata['refunded_at'] = timezone.now().isoformat()
        payment.save()
        
        # Update booking status
        payment.booking.status = 'cancelled'
        payment.booking.save()
        
        logger.info(f"Payment {payment_id} refunded")
        
        return Response({
            'message': 'Payment refunded successfully',
            'refund_id': refund.id
        })
        
    except Payment.DoesNotExist:
        return Response(
            {'error': 'Payment not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except stripe.error.StripeError as e:
        logger.error(f"Refund error: {str(e)}")
        return Response(
            {'error': f'Refund failed: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )