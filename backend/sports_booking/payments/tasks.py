from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.db.models import Count
from .models import Payment
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_payment_confirmation_email(payment_id):
    """Send payment confirmation mail to user"""
    try:
        payment = Payment.objects.select_related('booking__user', 'booking__club', 'booking__sport').get(id=payment_id)
        user = payment.booking.user
        booking = payment.booking

        if user.email:
            subject = f'Payment Confirmation - Booking #{booking.id}'
            message = f'''
            Dear {user.first_name or 'Customer'},

            Your payment has been successfully processed!

            Payment Details:
            - Booking ID: {booking.id}
            - Amount: ₹{payment.amount}
            - Club: {booking.club.name}
            - Date: {booking.date}
            - Time: {booking.start_time} - {booking.end_time}
            - Sport: {booking.sport.name}

            Please arrive 15 minutes before your slot time.

            Thank you for booking with us!

            Best regards,
            Sports Club Team
            '''

            send_mail(
                subject,
                message,
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@sportsclub.com'),
                [user.email],
                fail_silently=True,
            )
            return f"Email sent successfully to {user.email}"

        return "User has no email on file"

    except Payment.DoesNotExist:
        return f"Payment with ID {payment_id} not found"
    except Exception as e:
        logger.error(f"Failed to send payment confirmation email: {str(e)}")
        return f"Failed to send email: {str(e)}"


@shared_task
def cleanup_expired_payments():
    """Periodic task: mark stale, never-completed payments as failed and
    release their bookings so the slot becomes available again.

    A Payment is considered stale if it's still 'pending' and was created
    more than SLOT_LOCK_DURATION (plus a grace window) ago — matching how
    bookings.tasks.release_expired_slot_locks already treats stale locks.
    """
    try:
        cutoff_time = timezone.now() - timedelta(hours=1)
        expired_payments = Payment.objects.select_related('booking').filter(
            created_at__lt=cutoff_time,
            status='pending',
        )

        count = 0
        for payment in expired_payments:
            with transaction.atomic():
                payment.status = 'failed'
                payment.failed_at = timezone.now()
                payment.failure_reason = 'Payment not completed within the allowed window'
                payment.save(update_fields=['status', 'failed_at', 'failure_reason'])

                booking = payment.booking
                if booking.status == 'pending':
                    booking.status = 'cancelled'
                    booking.cancellation_reason = 'Payment timed out'
                    booking.cancelled_at = timezone.now()
                    booking.save(update_fields=['status', 'cancellation_reason', 'cancelled_at', 'updated_at'])
            count += 1

        logger.info(f"Cleaned up {count} expired payments")
        return f"Successfully cleaned up {count} expired payments"

    except Exception as e:
        logger.error(f"Expired payments cleanup failed: {e}")
        return f"Cleanup failed: {str(e)}"


@shared_task
def security_monitoring():
    """Flag users/bookings with repeated failed payments in the last hour.

    The old implementation relied on `attempts` / `last_attempt_at` counter
    fields that don't exist on the Payment model. This version derives the
    same signal from actual Payment rows instead.
    """
    try:
        cutoff = timezone.now() - timedelta(hours=1)
        suspicious = (
            Payment.objects.filter(status='failed', failed_at__gte=cutoff)
            .values('booking__user_id', 'booking__user__username')
            .annotate(failure_count=Count('id'))
            .filter(failure_count__gte=3)
        )

        suspicious_list = list(suspicious)
        if suspicious_list:
            logger.warning(f"Detected {len(suspicious_list)} user(s) with repeated payment failures: {suspicious_list}")

        return f"Security check completed. {len(suspicious_list)} user(s) flagged."

    except Exception as e:
        logger.error(f"Security monitoring failed: {e}")
        return f"Security monitoring failed: {str(e)}"