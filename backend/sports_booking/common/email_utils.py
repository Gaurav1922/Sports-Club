import logging
import resend
from django.conf import settings

logger = logging.getLogger(__name__)

resend.api_key = settings.RESEND_API_KEY


def send_resend_email(subject, message, to_email, from_email=None):
    """
    Send an email via Resend's HTTP API instead of SMTP.
    Returns the Resend response dict on success, or None on failure
    (mirrors send_mail's fail_silently=True behavior — callers already
    check truthiness of the return value).
    """
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set, skipping email to %s", to_email)
        return None
    try:
        result = resend.Emails.send({
            "from": from_email or settings.DEFAULT_FROM_EMAIL,
            "to": [to_email],
            "subject": subject,
            "text": message,
        })
        return result
    except Exception as e:
        logger.error("Resend send failed for %s: %s", to_email, e)
        return None