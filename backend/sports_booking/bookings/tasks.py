from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_booking_confirmation_email(booking_id):
    """Send booking confirmation email to user"""
    try:
        from bookings.models import Booking
        booking = Booking.objects.select_related('user', 'club', 'sport').get(id=booking_id)
        user = booking.user

        if not user.email:
            logger.info(f"No email for user {user.username}, skipping confirmation email")
            return "No email address"

        subject = f'Booking Confirmed - {booking.club.name}'
        message = f"""
Dear {user.first_name or user.username},

Your booking has been confirmed!

Booking Details:
- Club: {booking.club.name}
- Sport: {booking.sport.name}
- Date: {booking.date}
- Time: {booking.start_time} - {booking.end_time}
- Amount: ₹{booking.amount}

Please arrive 15 minutes before your slot time.

Thank you for booking with Sports Club!

Best regards,
Sports Club Team
        """

        send_mail(
            subject,
            message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@sportsclub.com'),
            [user.email],
            fail_silently=True,
        )
        logger.info(f"Confirmation email sent to {user.email} for booking {booking_id}")
        return f"Email sent to {user.email}"

    except Exception as e:
        logger.error(f"Failed to send confirmation email for booking {booking_id}: {e}")
        return f"Failed: {str(e)}"


@shared_task
def send_booking_confirmation_sms(booking_id):
    """Send booking confirmation SMS to user"""
    try:
        from bookings.models import Booking
        booking = Booking.objects.select_related('user', 'club', 'sport').get(id=booking_id)
        user = booking.user

        if not user.mobile_number:
            logger.info(f"No mobile for user {user.username}, skipping SMS")
            return "No mobile number"

        # Only send if Twilio is configured
        twilio_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        twilio_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        twilio_from = getattr(settings, 'TWILIO_PHONE_NUMBER', None)

        if not all([twilio_sid, twilio_token, twilio_from]) or twilio_sid == 'None':
            logger.info(f"Twilio not configured, skipping SMS for booking {booking_id}")
            return "Twilio not configured"

        from twilio.rest import Client
        client = Client(twilio_sid, twilio_token)
        message = client.messages.create(
            body=(
                f"Booking Confirmed! {booking.club.name} - {booking.sport.name} "
                f"on {booking.date} at {booking.start_time}. Amount: ₹{booking.amount}"
            ),
            from_=twilio_from,
            to=f"+91{user.mobile_number}"
        )
        logger.info(f"SMS sent to {user.mobile_number} for booking {booking_id}")
        return f"SMS sent: {message.sid}"

    except Exception as e:
        logger.error(f"Failed to send SMS for booking {booking_id}: {e}")
        return f"Failed: {str(e)}"


@shared_task
def send_otp_sms_task(mobile_number, otp_code):
    """Send OTP via SMS"""
    try:
        twilio_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        twilio_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        twilio_from = getattr(settings, 'TWILIO_PHONE_NUMBER', None)

        if not all([twilio_sid, twilio_token, twilio_from]) or twilio_sid == 'None':
            logger.info(f"DEV OTP for {mobile_number}: {otp_code}")
            print(f"\n{'='*40}\nDEV OTP for {mobile_number}: {otp_code}\n{'='*40}\n")
            return "Dev mode - OTP logged"

        from twilio.rest import Client
        client = Client(twilio_sid, twilio_token)
        message = client.messages.create(
            body=f"Your Sports Club OTP is: {otp_code}. Valid for 10 minutes.",
            from_=twilio_from,
            to=f"+91{mobile_number}"
        )
        return f"OTP SMS sent: {message.sid}"

    except Exception as e:
        logger.error(f"Error sending OTP SMS to {mobile_number}: {e}")
        return f"Failed: {str(e)}"


@shared_task
def send_welcome_email_task(user_id):
    """Send welcome email to new user"""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=user_id)

        if not user.email:
            return "No email address"

        send_mail(
            subject='Welcome to Sports Club!',
            message=f"""
Dear {user.first_name or user.username},

Welcome to Sports Club! Your account has been created successfully.

You can now browse and book sports facilities at your favorite clubs.

Best regards,
Sports Club Team
            """,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@sportsclub.com'),
            recipient_list=[user.email],
            fail_silently=True,
        )
        return f"Welcome email sent to {user.email}"

    except Exception as e:
        logger.error(f"Failed to send welcome email: {e}")
        return f"Failed: {str(e)}"


@shared_task
def release_expired_slot_locks():
    """Periodic task: release expired slot locks and cancel pending bookings"""
    try:
        from bookings.models import SlotLock, Booking
        expired_locks = SlotLock.objects.filter(
            expires_at__lt=timezone.now(),
            is_converted=False
        )
        count = expired_locks.count()
        for lock in expired_locks:
            Booking.objects.filter(
                club=lock.club,
                sport=lock.sport,
                date=lock.date,
                start_time=lock.start_time,
                status='pending'
            ).update(status='cancelled')
        expired_locks.delete()

        # Also cancel stale pending bookings older than 15 minutes
        cutoff = timezone.now() - timedelta(minutes=15)
        stale_count = Booking.objects.filter(
            status='pending',
            created_at__lt=cutoff
        ).update(status='cancelled')

        logger.info(f"Released {count} expired locks, cancelled {stale_count} stale bookings")
        return f"Released {count} locks, cancelled {stale_count} bookings"

    except Exception as e:
        logger.error(f"Slot lock cleanup failed: {e}")
        return f"Failed: {str(e)}"