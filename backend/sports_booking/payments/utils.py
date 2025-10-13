from django.conf import settings
import qrcode
from io import BytesIO
from django.core.files import File
import hashlib
import hmac
import json

class PaymentUtils:

    @staticmethod
    def generate_upi_ar_string(upi_id, amount,transaction_id, merchant_name="Sports Club"):
        """Generate UPI QR code string"""
        upi_string = (
            f"upi://pay?"
            f"pa={upi_id}&"
            f"pn={merchant_name}&"
            f"am={amount}&"
            f"tn=Booking-{transaction_id}&"
            f"cu=INR"
        )
        return upi_string
        
    @staticmethod
    def generate_qr_code_image(data_string):
        """Generate QR code image from string"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data_string)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return buffer
    
    @staticmethod
    def verify_webhook_signature(payload, signature, secret_key):
        """Verify webhook signature from payment gateway"""
        expected_signature = hmac.new(
            secret_key.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    @staticmethod
    def format_amount_for_display(amount):
        """Format amount for display (₹1,234.56)"""
        return f"₹{amount:,.2f}"

# Updated payments/models.py (add method to Payment model)
# Add this method to your existing Payment model