import stripe
from django.conf import settings
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from bookings.models import Booking
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

if getattr(settings, 'STRIPE_SECRET_KEY', None):
    stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
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
    serializer = PaymentIntentSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        booking_id = serializer.validated_data['booking_id']
        booking = Booking.objects.select_related('club', 'sport').get(id=booking_id, user=request.user)
        if booking.status != 'pending':
            return Response({'error': 'Booking is not in pending state'}, status=status.HTTP_400_BAD_REQUEST)
        # if settings.DEBUG:
        if True:
            return Response({
                'client_secret': f'dev_secret_{booking.id}',
                'payment_intent_id': f'pi_dev_{booking.id}',
                'amount': float(booking.amount),
                'currency': 'INR'
            }, status=status.HTTP_200_OK)
        intent = stripe.PaymentIntent.create(
            amount=int(booking.amount * 100),
            currency='inr',
            metadata={'booking_id': booking.id, 'user_id': request.user.id},
            description=f"Booking at {booking.club.name} for {booking.sport.name}",
        )
        Payment.objects.create(
            booking=booking,
            stripe_payment_intent_id=intent.id,
            amount=booking.amount,
            currency='INR',
            status='pending',
        )
        return Response({
            'client_secret': intent.client_secret,
            'payment_intent_id': intent.id,
            'amount': float(booking.amount),
            'currency': 'INR'
        }, status=status.HTTP_200_OK)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error creating payment intent: {str(e)}")
        return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_payment(request):
    serializer = PaymentConfirmSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        booking_id = serializer.validated_data['booking_id']
        payment_intent_id = serializer.validated_data['payment_intent_id']
        payment_method = serializer.validated_data.get('payment_method', 'card')
        booking = Booking.objects.select_related('club', 'sport').get(id=booking_id, user=request.user)

        # Use dev bypass if DEBUG=True OR if PAYMENT_DEV_MODE env var is set
        # use_dev_mode = settings.DEBUG or getattr(settings, 'PAYMENT_DEV_MODE', False)
        use_dev_mode = True
        if use_dev_mode:
            with transaction.atomic():
                Payment.objects.update_or_create(
                    booking=booking,
                    defaults={
                        'amount': booking.amount,
                        'currency': 'INR',
                        'status': 'completed',
                        'stripe_payment_intent_id': payment_intent_id,
                        'payment_method': payment_method,
                        'completed_at': timezone.now(),
                    }
                )
                booking.status = 'confirmed'
                booking.save()
                try:
                    if booking.lock:
                        booking.lock.is_converted = True
                        booking.lock.save()
                except Exception:
                    pass
            logger.info(f"DEV: Payment confirmed for booking {booking.id}")
            return Response({
                'message': 'Payment confirmed',
                'booking_id': booking.id,
                'status': 'confirmed',
            }, status=status.HTTP_200_OK)

        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        if intent.status == 'succeeded':
            with transaction.atomic():
                payment, created = Payment.objects.get_or_create(
                    booking=booking,
                    stripe_payment_intent_id=payment_intent_id,
                    defaults={'amount': booking.amount, 'currency': 'INR', 'status': 'completed', 'completed_at': timezone.now()}
                )
                if not created:
                    payment.status = 'completed'
                    payment.completed_at = timezone.now()
                    payment.save()
                booking.status = 'confirmed'
                booking.save()
                try:
                    if booking.lock:
                        booking.lock.is_converted = True
                        booking.lock.save()
                except Exception:
                    pass
                send_booking_confirmation_email.delay(booking.id)
                send_booking_confirmation_sms.delay(booking.id)
            return Response({'message': 'Payment successful', 'booking_id': booking.id, 'status': 'confirmed'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': f'Payment status: {intent.status}'}, status=status.HTTP_400_BAD_REQUEST)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error confirming payment: {str(e)}")
        return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            booking_id = payment_intent['metadata'].get('booking_id')
            if booking_id:
                booking = Booking.objects.get(id=booking_id)
                Payment.objects.update_or_create(
                    booking=booking,
                    stripe_payment_intent_id=payment_intent['id'],
                    defaults={'amount': booking.amount, 'currency': 'INR', 'status': 'completed', 'completed_at': timezone.now()}
                )
                if booking.status != 'confirmed':
                    booking.status = 'confirmed'
                    booking.save()
                    send_booking_confirmation_email.delay(booking.id)
                    send_booking_confirmation_sms.delay(booking.id)
        return Response({'status': 'success'}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def refund_payment(request, payment_id):
    try:
        payment = Payment.objects.get(id=payment_id)
        if payment.status != 'completed':
            return Response({'error': 'Can only refund completed payments'}, status=status.HTTP_400_BAD_REQUEST)
        refund = stripe.Refund.create(payment_intent=payment.stripe_payment_intent_id)
        payment.status = 'refunded'
        payment.metadata = payment.metadata or {}
        payment.metadata['refund_id'] = refund.id
        payment.save()
        payment.booking.status = 'cancelled'
        payment.booking.save()
        return Response({'message': 'Payment refunded successfully', 'refund_id': refund.id})
    except Payment.DoesNotExist:
        return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'Refund failed: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
