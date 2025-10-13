from celery import shared_task
from twilio.rest import Client
from django.conf import settings
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_otp_sms(phone_number, otp):
    # Send OTP via SMS using Twilio
    try:
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
            logger.warning(f"Twilio not configured. OTP for {phone_number}: {otp}")
            return f"OTP logged for {phone_number}: {otp}"
        
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        message = client.messages.create(
            body=f'Your OTP for Sports Club booking is: {otp}. Valid for 10 minutes.',
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number
        )

        logger.info(f"SMS sent successfully to {phone_number}: {message.sid}")
        return f"SMS sent successfully: {message.sid}"
    
    except Exception as e:
        logger.error(f"Failed to send SMS to {phone_number}: {str(e)}")
        return f"Failed to send SMS: {str(e)}"

@shared_task
def send_welcome_email(user_id):
    # Send welcome email to new user
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=user_id)

        if user.email:
            subject = 'Welcome to Sports Club Booking!'
            message = f'''
            Hello {user.firsr_name or 'Sports Enthuiast'},
            Welcome to our Sports Club Booking platform!

            You can now:
            - Browse nearby sports clubs
            - Book time slots for your favorite sports
            - make secure payments
            - Track your booking history

            Happy Playing😊!

            Team Sports Club Booking
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
    