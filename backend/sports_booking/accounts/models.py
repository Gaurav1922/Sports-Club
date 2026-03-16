from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    # Custom user model with mobile number
    mobile_number = models.CharField(
        max_length=10,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\d{10}$', message='Enter a valid 10-digit mobile number'
            )
        ]
    )
    email = models.EmailField(unique=True)
    is_mobile_verified = models.BooleanField(default=False)
    
    # Added USERNAME_FIELD and REQUIRED_FIELDS — Django requires these
    # when using a custom user model with a non-default auth field
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'mobile_number']
    
    
    class Meta:
        db_table = 'users'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['mobile_number']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return self.username
    
    def get_full_name(self):
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name if full_name else self.username
    
    # Added property for total bookings count — used by profile API
    @property
    def total_booking(self):
        return self.bookings.count()

class OTP(models.Model):
    mobile_number = models.CharField(max_length=10)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    # Track how many times OTP was attempted - Prevents brute force
    attempts = models.PositiveSmallIntegerField(default=0)
    
    MAX_ATTEMPTS = 3 # Constant for max OTP verification attempts

    class Meta:
        db_table = 'otp_records'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['mobile_number', 'is_verified']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.mobile_number} - {self.otp}"
    
    @property
    def is_expired(self):
        # check if otp expired
        return timezone.now() > self.expires_at
    
    # Added is_valid property combining expired + attempted checks
    @property
    def is_valid(self):
        return not self.is_expired and not self.is_verified and self.attempts < self.MAX_ATTEMPTS
    
    def save(self, *args, **kwargs):
        # Auto-set expiration time if not provided
        if not self.expires_at:
            from datetime import timedelta
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)