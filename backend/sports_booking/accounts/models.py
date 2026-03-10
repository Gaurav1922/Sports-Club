from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone


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

class OTP(models.Model):
    mobile_number = models.CharField(max_length=10)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)

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
    
    def save(self, *args, **kwargs):
        # Auto-set expiration time if not provided
        if not self.expires_at:
            from datetime import timedelta
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)