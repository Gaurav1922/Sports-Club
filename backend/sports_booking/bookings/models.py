from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
import uuid

User = get_user_model()

# Create your models here.

class SlotLock(models.Model):
    """Temporary lock on time slot during booking process"""
    club = models.ForeignKey('clubs.Club', on_delete=models.CASCADE)
    sport = models.ForeignKey('clubs.Sport', on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    locked_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_converted = models.BooleanField(default=False)   # Converted to booking

    class Meta:
        db_table = 'slot_locks'
        unique_together = ['club', 'sport', 'date', 'start_time', 'end_time']
        indexes = [
            models.Index(fields=['expires_at']),
            models.Index(fields=['is_converted']),
            models.Index(fields=['user', 'is_converted']),
        ]

    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(
                seconds=getattr(settings, 'SLOT_LOCK_DURATION', 600)
            )
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.club.name} - {self.date} {self.start_time}"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    club = models.ForeignKey('clubs.Club', on_delete=models.CASCADE)
    sport = models.ForeignKey('clubs.Sport', on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    lock = models.ForeignKey(SlotLock, on_delete=models.SET_NULL, null=True, blank=True, related_name='booking')

    """# Cancellation details
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)

    # Admin Fields
    admin_notes = models.TextField(blank=True)"""

    class Meta:
        db_table = 'bookings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['date', 'club']),
            models.Index(fields=['status', 'date']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.club.name} - {self.date}"
    
class SlotWaitlist(models.Model):
    # track user who tried to book a locked slot
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='waitlisted_slots')
    club = models.ForeignKey('clubs.Club', on_delete=models.CASCADE)
    sport = models.ForeignKey('clubs.Sport', on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    notified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'slot_waitlist'
        ordering = ['created_at']   # First come, first notified
        indexes = [
            models.Index(fields=['club', 'sport', 'date', 'start_time']),
            models.Index(fields=['notified', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} waiting for {self.club.name} - {self.date} {self.start_time}"
    