from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Payment
from django.core.management import call_command
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_payment_confirmation_email(payment_id):
    """Send payment confirmation mail to user"""
    try:
        payment = Payment.objects.get(id=payment_id)
        user = payment.booking.user

        if user.email:
            subject = f'Payment Confirmation - {payment.transaction_id}'
            message = f'''
            Dear {user.first_name or 'Customer'},
            
            Your payment has been successfully processed!
            
            Payment Details:
            - Transaction ID: {payment.transaction_id}
            - Amount: ₹{payment.amount}
            - Club: {payment.booking.club.name}
            - Date: {payment.booking.time_slot.date}
            - Time: {payment.booking.time_slot.start_time} - {payment.booking.time_slot.end_time}
            - Sport: {payment.booking.time_slot.sport}

            Please arrive 15 minutes before your slot time.
            
            Thank you for booking with us!
            
            Best regards,
            Sports Club Team
            '''

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@sportsclub.com',
                [user.email],
                fail_silently=False,
            )
        
        return f"Email sent successfully to {user.email if user.email else 'no email'}"
    
    except Payment.DoesNotExist:
        return f"Payment with ID {payment_id} not found"
    except Exception as e:
        logger.error(f"Failed to send payment confirmation email: {str(e)}")
        return f"Failed to send email: {str(e)}"
    
@shared_task
def process_payment_refund(payment_id):
    #Process payment refund asynchronously
    try:
        payment = Payment.objects.get(id=payment_id)
        
        # Here you would integrate with actual payment gateway
        # to process the refund
        
        # For now, just mark as refunded
        payment.status = 'refunded'
        payment.save()

        # Update booking
        booking = payment.booking
        booking.payment_status = 'refunded'
        booking.save()
        
        # Send refund confirmation email
        send_payment_confirmation_email.delay(payment_id)
        
        return f"Refund processed for payment {payment.transaction_id}"
    
    except Payment.DoesNotExist:
        return f"Payment with ID {payment_id} not found"
    except Exception as e:
        logger.error(f"Failed to process refund: {str(e)}")
        return f"Failed to process refund: {str(e)}"
    

@shared_task
def cleanup_expired_payments():
    # Periodic task to clean up expired payments
    
    try:
        cutoff_time = timezone.now() -timedelta(hours=1)
        expired_payments = Payment.objects.filter(
            expires_at__lt=cutoff_time,
            status='pending'
        )

        count = 0
        for payment in expired_payments:
            if payment.qr_code:
                try:
                    payment.qr_code.delete()
                except Exception as e:
                    logger.error(f"Failed to delete QR code for {payment.transaction_id}: {e}")
            
            payment.status = 'expired'
            payment.save()
            count += 1
        
        logger.info(f"Cleaned up {count} expired payments")
        return f"Successfully cleaned up {count} expired payments"
    
    except Exception as e:
        logger.error(f"Expired payments cleanup failed: {e}")
        return f"Cleanup failed: {str(e)}"

@shared_task
def security_monitoring():
    # Monitor for suspicious payment activities"""

    # Check for multiple failed attempts from same user
    try:
        suspicious_activities = Payment.objects.filter(
            attempts__gte=3,
            last_attempt_at__gte=timezone.now() - timedelta(hours=1)
        )
    
        if suspicious_activities.exists():
            logger.warning(f"Detected {suspicious_activities.count()} payments with suspicious activity")
        
        # Here you could send alerts to admins
        # send_security_alert.delay(list(suspicious_activities.values_list('id', flat=True)))
    
        return f"Security check completed. {suspicious_activities.count()} suspicious activities detected."
    
    except Exception as e:
        logger.error(f"Security monitoring failed: {e}")
        return f"Security monitoring failed: {str(e)}"
    