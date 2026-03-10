from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_otp_sms_task(mobile_number, otp):
    # Send OTP via SMS using Twilio
    try:
        from twilio.rest import Client

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        message_body = (
            f"Your Sports Club OTP is {otp}\n"
            f"Valid for 10 minutes.\n"
            f"Do not share this code with anyone."
        )

        message = client.messages.create(
            body=message_body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=f"+91{mobile_number}"
        )

        logger.info(f"OTP SMS sent to {mobile_number}: {message.sid}")
        return f"OTP SMS sent: {message.sid}"
    
    except Exception as e:
        logger.error(f"Error sending OTP SMS to {mobile_number}: {str(e)}")
        return f"Error sending OTP SMS: {str(e)}"

@shared_task
def send_welcome_email_task(user_id):
    # Send welcome email to new user
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user = User.objects.get(id=user_id)

        if user.email:
            subject = 'Welcome to Sports Club!'
            message = f'''
            Hello {user.first_name or 'Sports Enthuiast'},
            Welcome to our Sports Club! platform!

            You can now:
            - Browse nearby sports clubs
            - Book time slots for your favorite sports
            - make secure payments
            - Track your booking history

            Happy Playing😊!

            Team Sports Club Team
            '''

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            return f"Welcome email sent to {user.email}"
    except Exception as e:
        logger.error(f"Failed to send welcome email: {str(e)}")
        return f"Failed to send welcome email: {str(e)}"
    