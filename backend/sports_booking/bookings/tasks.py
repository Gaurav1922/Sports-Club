from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_booking_confirmation_email(booking_id):
    """Send booking confirmation email"""
    try:
        from .models import Booking
        booking = Booking.objects.select_related('user', 'club', 'sport').get(id=booking_id)
        
        subject = f'Booking Confirmed - {booking.club.name}'
        message = f"""
        Dear {booking.user.first_name},
        
        Your booking has been confirmed!
        
        Booking Details:
        ----------------
        Booking ID: {booking.id}
        Club: {booking.club.name}
        Location: {booking.club.location}
        Sport: {booking.sport.name}
        Date: {booking.date.strftime('%d %B, %Y')}
        Time: {booking.start_time.strftime('%I:%M %p')} - {booking.end_time.strftime('%I:%M %p')}
        Amount: ₹{booking.amount}
        
        Please arrive 10 minutes before your booking time.
        
        If you have any questions, please contact us.
        
        Best regards,
        Sports Club Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [booking.user.email],
            fail_silently=False,
        )
        logger.info(f"Confirmation email sent to {booking.user.email} for booking {booking_id}")
        return f"Email sent to {booking.user.email}"
    except Exception as e:
        logger.error(f"Error sending confirmation email for booking {booking_id}: {str(e)}")
        return f"Error sending email: {str(e)}"

@shared_task
def send_booking_confirmation_sms(booking_id):
    """Send booking confirmation SMS via Twilio"""
    try:
        from twilio.rest import Client
        from .models import Booking
        
        booking = Booking.objects.select_related('user', 'club', 'sport').get(id=booking_id)
        
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        message_body =(
            f"Booking Confirmed!\n"
            f"{booking.club.name}\n"
            f"Date: {booking.date.strftime('%d-%m-%Y')}\n"
            f"Time: {booking.start_time.strftime('%I:%M %p')}\n"
            f"Booking ID: {booking.id}"
        )
        
        message = client.messages.create(
            body=message_body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=f"+91{booking.user.mobile_number}"
        )
        
        logger.info(f"Confirmation SMS sent to {booking.user.mobile_number} for booking {booking_id}")
        return f"SMS sent: {message.sid}"
    except Exception as e:
        logger.error(f"Error sending confirmation SMS for booking {booking_id}: {str(e)}")
        return f"Error sending SMS: {str(e)}"

@shared_task
def send_otp_sms_task(mobile_number, otp):
    """Send OTP via SMS"""
    try:
        from twilio.rest import Client
        
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        message_body = f"Your Sports Club OTP is: {otp}\nValid for 10 minutes.\nDo not share this code."

        message = client.messages.create(
            body=message_body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=f"+91{mobile_number}"
        )
        
        logger.info(f"OTP SMS sent to {mobile_number}")
        return f"OTP SMS sent: {message.sid}"
    except Exception as e:
        logger.error(f"Error sending OTP SMS to {mobile_number}: {str(e)}")
        return f"Error sending OTP SMS: {str(e)}"
    
@shared_task
def cleanup_expired_locks():
    """Periodic task to clean up expired slot locks and notify waitlisted users"""
    try:
        from .models import SlotLock
        
        expired_locks = SlotLock.objects.filter(
            expires_at__lt=timezone.now(),
            is_converted=False
        ).select_related('club', 'sport')
        
        # Store lock details before deletion for notifications
        locks_to_notify = []
        for lock in expired_locks:
            locks_to_notify.append({
                'club_id': lock.club.id,
                'sport_id': lock.sport.id,
                'date': lock.date.strftime('%Y-%m-%d'),
                'start_time': str(lock.start_time),
                'end_time': str(lock.end_time),
            })
        
        count = expired_locks.count()
        expired_locks.delete()
        
        # Notify waitlisted users for each expired lock
        for lock_info in locks_to_notify:
            notify_waitlisted_users.delay(
                lock_info['club_id'],
                lock_info['sport_id'],
                lock_info['date'],
                lock_info['start_time'],
                lock_info['end_time']
            )
        
        logger.info(f"Deleted {count} expired locks and queued notifications")
        return f"Deleted {count} expired locks, notified waitlisted users"
    except Exception as e:
        logger.error(f"Error cleaning up expired locks: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def send_booking_status_update(booking_id, status):
    """Notify user about booking status change"""
    try:
        from .models import Booking
        from twilio.rest import Client
        
        booking = Booking.objects.select_related('user', 'club').get(id=booking_id)
        
       # Send Email
        subject = f'Booking {status.title()} - {booking.club.name}'
        message = f"""
Dear {booking.user.first_name},

Your booking status has been updated.

Booking ID: {booking.id}
Club: {booking.club.name}
Status: {status.upper()}

If you have any questions, please contact us.

Best regards,
Sports Club Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [booking.user.email],
            fail_silently=False,
        )
        
        # Send SMS
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        sms_body = f"Booking #{booking.id} status updated to: {status.upper()}"

        client.messages.create(
            body=sms_body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=f"+91{booking.user.mobile_number}"
        )
        
        logger.info(f"Status update notifications sent for booking {booking_id}")
        return f"Status update notifications sent for booking {booking_id}"
    except Exception as e:
        logger.error(f"Error sending status update for booking {booking_id}: {str(e)}")
        return f"Error: {str(e)}"

@shared_task
def send_welcome_email_task(user_id):
    """Send welcome email to new user"""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user = User.objects.get(id=user_id)
        
        subject = 'Welcome to Sports Club!'
        message = f"""
Dear {user.first_name},

Welcome to Sports Club!

Your account has been successfully created. You can now:
- Browse available sports clubs
- Book your favorite sports facilities
- Manage your bookings
- Leave reviews and ratings

Start exploring and book your next game today!

Best regards,
Sports Club Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        logger.info(f"Welcome email sent to {user.email}")
        return f"Welcome email sent to {user.email}"
    except Exception as e:
        logger.error(f"Error sending welcome email to user {user_id}: {str(e)}")
        return f"Error: {str(e)}"
    
    
@shared_task
def notify_waitlisted_users(club_id, sport_id, date_str, start_time_str, end_time_str):
    """Notify users on waitlist when a slot becomes available"""
    try:
        from .models import SlotWaitlist
        from datetime import datetime
        
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get all users waiting for this slot who haven't been notified
        waitlist = SlotWaitlist.objects.filter(
            club_id=club_id,
            sport_id=sport_id,
            date=date,
            start_time=start_time_str,
            notified=False
        ).select_related('user', 'club', 'sport').order_by('created_at')
        
        if not waitlist.exists():
            return "No users on waitlist"
        
        notifications_sent = 0
        
        for entry in waitlist:
            # Send SMS notification
            try:
                from twilio.rest import Client
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                
                message_body = (
                    f"Good news! The slot you wanted is now available:\n"
                    f"{entry.club.name}\n"
                    f"Sport: {entry.sport.name}\n"
                    f"Date: {entry.date.strftime('%d-%m-%Y')}\n"
                    f"Time: {entry.start_time.strftime('%I:%M %p')}\n"
                    f"Book now before it's gone!"
                )
                
                client.messages.create(
                    body=message_body,
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=f"+91{entry.user.mobile_number}"
                )
                
                logger.info(f"Slot availability SMS sent to {entry.user.mobile_number}")
            except Exception as e:
                logger.error(f"Error sending SMS to {entry.user.mobile_number}: {str(e)}")
            
            # Send Email notification
            try:
                subject = f"Slot Available - {entry.club.name}"
                message = f"""
Dear {entry.user.first_name},

Great news! The slot you previously tried to book is now available:

Slot Details:
-------------
Club: {entry.club.name}
Location: {entry.club.location}
Sport: {entry.sport.name}
Date: {entry.date.strftime('%d %B, %Y')}
Time: {entry.start_time.strftime('%I:%M %p')} - {entry.end_time.strftime('%I:%M %p')}
Price: ₹{entry.sport.price_per_hour}

This slot was previously locked by another user who didn't complete the payment.

Book now before someone else takes it!

Login here: http://localhost:3000

Best regards,
Sports Club Team
                """
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [entry.user.email],
                    fail_silently=False,
                )
                
                logger.info(f"Slot availability email sent to {entry.user.email}")
            except Exception as e:
                logger.error(f"Error sending email to {entry.user.email}: {str(e)}")
            
            # Mark as notified
            entry.notified = True
            entry.save()
            notifications_sent += 1
        
        logger.info(f"Notified {notifications_sent} users about available slot")
        return f"Notified {notifications_sent} users"
        
    except Exception as e:
        logger.error(f"Error notifying waitlisted users: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def cleanup_old_waitlist_entries():
    """Clean up old waitlist entries (older than 7 days)"""
    try:
        from .models import SlotWaitlist
        from datetime import timedelta
        
        cutoff_date = timezone.now().date() - timedelta(days=7)
        
        deleted_count = SlotWaitlist.objects.filter(
            date__lt=cutoff_date
        ).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} old waitlist entries")
        return f"Deleted {deleted_count} old waitlist entries"
    except Exception as e:
        logger.error(f"Error cleaning up waitlist: {str(e)}")
        return f"Error: {str(e)}"