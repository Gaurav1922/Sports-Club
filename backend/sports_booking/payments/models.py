from django.db import models
from bookings.models import Booking
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from django.utils import timezone
from datetime import timedelta
import secrets
import hashlib
from PIL import Image, ImageDraw

# Create your models here.

class Payment(models.Model):
   # PAYMENT_METHOD_CHOICES = [
   #     ('qr', 'QR Code'),
   #     ('upi', 'UPI'),
   #     ('card', 'Card'),
   #     ('wallet', 'Wallet'),
    #]

    PAYMENT_METHOD_CHOICES = [
        ('stripe_card', 'Credit/Debit Card'),
        ('stripe_wallet', 'Digital Wallet'),
        ('upi', 'UPI'),  # Keep for local payments
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
        ('refunded', 'Refunded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created = models.DateTimeField(auto_now_add=True)
    
    # Security Fields
    qr_code_hash = models.CharField(max_length=64, blank=True)  # SHA256 hash for integrity
    security_token = models.CharField(max_length=32, blank=True)  # For QR validation
    expires_at = models.DateTimeField(default=timezone.now)  # QR code expiration
    attempts = models.IntegerField(default=0)  # Failed verification attempts
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    is_locked = models.BooleanField(default=False)  # After too many failed attempts
    
    # Payment Details
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    upi_id = models.CharField(max_length=100, default='sportsclub@upi')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Admin only fields
    admin_notes = models.TextField(blank=True)  # For admin investigation
    created_by_admin = models.BooleanField(default=False)

    # Stripe specific fields
    stripe_payment_intent_id = models.CharField(max_length=200, blank=True)
    stripe_client_secret = models.CharField(max_length=200, blank=True)
    card_last_four = models.CharField(max_length=4, blank=True)
    card_brand = models.CharField(max_length=20, blank=True)
    

    class Meta:
        db_table = 'payments_payment'
        ordering = ['-created']
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = self.generate_transaction_id()
        
        if not self.expires_at:
            # QR codes expire in 10 minutes
            self.expires_at = timezone.now + timedelta(minutes=10)
        
        if not self.security_token:
            self.security_token = secrets.token_urlsafe(16)
        
        super().save(*args, **kwargs)
    
    def generate_transaction_id(self):
        """Generate unique transaction ID"""
        prefix = "TXN"
        timestamp = str(int(timezone.now().timestamp()))
        random_part = secrets.token_urlsafe(6)
        return f"{prefix}{timestamp}{random_part}".upper()
    
    def is_expired(self):
        """Check if payment has expired"""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    """def can_generate_new_qr(self):
        # Check if new QR can be generated (admin only or expired)
        return self.is_expired() or self.created_by_admin"""
    
    def generate_qr_code(self, force_regenerate=False, admin_user=None):
        """Generate QR code with security measures"""
        if not force_regenerate and self.qr_code and not self.is_expired():
            return False  # QR already exists and not expired
        
        if force_regenerate and not admin_user:
            return False  # Only admins can force regenerate
        
        if self.is_locked:
            return False  # Payment is locked due to security
        
        # Create secure UPI string with validation token
        upi_string = self.create_secure_upi_string()
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(upi_string)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Add watermark/security features
        img = self.add_security_watermark(img)
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Generate hash for integrity verification
        buffer_copy = BytesIO()
        img.save(buffer_copy, format='PNG')
        buffer_copy.seek(0)
        self.qr_code_hash = hashlib.sha256(buffer_copy.read()).hexdigest()
        
        # Save QR code
        filename = f'secure_qr_{self.transaction_id}_{secrets.token_urlsafe(8)}.png'
        if self.qr_code:
            self.qr_code.delete()  # Delete old QR code
        
        self.qr_code.save(filename, File(buffer), save=False)
        
        # Update expiration for new QR
        self.expires_at = timezone.now() + timedelta(minutes=10)
        
        # Log admin action if applicable
        if admin_user:
            self.admin_notes += f"\nQR regenerated by admin {admin_user} at {timezone.now()}"
            self.created_by_admin = True
        
        self.save()
        return True
    
    def create_secure_upi_string(self):
        return (
            f"upi://pay?"
            f"pa={self.upi_id}&"
            f"pn=SportsClub&"
            f"am={self.amount}&"
            f"tn={self.transaction_id}&"
            f"cu=INR&"
            f"mc=0000&tid={self.security_token}"
        )
    
        
        # Add security parameters (custom implementation)
        secure_params = f"&mc=0000&tid={self.security_token}"
        return base_upi + secure_params
    
    def add_security_watermark(self, img):
        """Add subtle security watermark to QR code"""
    
        
        # Convert to RGBA for watermark
        img = img.convert("RGBA")
        
        # Create watermark overlay
        overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        
        """# Add timestamp watermark (very subtle)
        timestamp = timezone.now().strftime("%Y%m%d%H%M")
        try:
            # This would work with proper font file
            # font = ImageFont.truetype("arial.ttf", 8)
            pass
        except:
            pass  # Use default font if custom font not available"""
        
        # Add subtle border pattern for authenticity
        width, height = img.size
        for i in range(0, width, 20):
            draw.line([(i, 0), (i, 2)], fill=(128, 128, 128, 50))
            draw.line([(i, height-2), (i, height)], fill=(128, 128, 128, 50))
        
        # Combine with original
        img = Image.alpha_composite(img, overlay)
        return img.convert("RGB")
    
    def verify_qr_integrity(self):
        """Verify QR code hasn't been tampered with"""

        if not self.qr_code or not self.qr_code_hash:
            return False
        
        try:
            with open(self.qr_code.path, 'rb') as qr_file:
                current_hash = hashlib.sha256(qr_file.read()).hexdigest()
                return current_hash == self.qr_code_hash
        except FileNotFoundError:
            return False
    
    def increment_attempts(self):
        """Increment failed verification attempts"""

        self.attempts += 1
        self.last_attempt_at = timezone.now()
        
        # Lock after 5 failed attempts
        
        if self.attempts >= 5:
            self.is_locked = True
            self.status = 'failed'
            self.admin_notes += f"\nPayment locked due to {self.attempts} failed attempts at {timezone.now()}"
        
        self.save()
    
    def can_process_payment(self):
        """Check if payment can be processed"""
        if self.is_locked:
            return False, "Payment is locked due to security violations"
        
        if self.is_expired():
            return False, "Payment has expired"
        
        if self.status != 'pending':
            return False, f"Payment status is {self.status}"
        
        if not self.verify_qr_integrity():
            return False, "QR code integrity check failed"
        
        return True, "OK"
    
    def __str__(self):
        return f"Payment {self.transaction_id} - {self.status}"




"""class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('qr', 'QR Code'),
        ('upi', 'UPI'),
        ('card', 'Card'),
        ('wallet', 'Wallet'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    upi_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)


    def generate_qr_code(self):
    # Generate QR code for UPI payment
        if self.payment_method == 'qr' and self.upi_id:
            from .utils import PaymentUtils
        
            # Generate UPI string
            upi_string = PaymentUtils.generate_upi_qr_string(
                upi_id=self.upi_id,
                amount=self.amount,
                transaction_id=self.transaction_id
            )
        
            # Generate QR code image
            qr_buffer = PaymentUtils.generate_qr_code_image(upi_string)
        
            # Save QR code image
            filename = f'qr_{self.transaction_id}.png'
            self.qr_code.save(
                filename,
                File(qr_buffer),
                save=False
            )
            
    
    def generate_qr_code(self):
        if self.payment_method == 'qr':
            upi_string = f"upi://pay?pa={self.upi_id}&pn=SportsClub&am={self.amount}&tn=Booking-{self.booking.id}"
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(upi_string)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)

            self.qr_code.save(
                f'qr_{self.transaction_id}.png',
                File(buffer),
                save=False
            )"""