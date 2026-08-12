from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.core.exceptions import ValidationError
import uuid

User = get_user_model()


class SlotLock(models.Model):
    """Temporary lock on a time slot while a user completes checkout."""
    club = models.ForeignKey('clubs.Club', on_delete=models.CASCADE)
    sport = models.ForeignKey('clubs.Sport', on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    locked_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_converted = models.BooleanField(default=False)  # Converted to a paid booking

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
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # unique=True: DB-level guarantee that a lock can never back two bookings,
    # even if application logic (is_converted checks) has a bug or races.
    lock = models.OneToOneField(
        SlotLock, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='booking'
    )

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

    def clean(self):
        super().clean()

        if self.start_time >= self.end_time:
            raise ValidationError(
                "start_time must be before end_time"
            )

        if self.date < timezone.now().date():
            raise ValidationError(
                "Booking date cannot be in the past"
            )

        overlapping = Booking.objects.filter(
            club=self.club,
            sport=self.sport,
            date=self.date,
            status__in=["pending", "confirmed"],
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
        )

        if self.pk:
            overlapping = overlapping.exclude(pk=self.pk)

        if overlapping.exists():
            raise ValidationError(
                "Selected slot is already booked."
            )

    def cancel(self, reason=""):
        if self.status == "cancelled":
            return

        self.status = "cancelled"
        self.cancelled_at = timezone.now()
        self.cancellation_reason = reason
        self.save()


class SlotWaitlist(models.Model):
    """Track users who tried to book a slot that was locked by someone else."""
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
        ordering = ["created_at"]  # First come, first notified
        unique_together = ['user', 'club', 'sport', 'date', 'start_time', 'end_time']
        indexes = [
            models.Index(fields=['club', 'sport', 'date', 'start_time']),
            models.Index(fields=['notified', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} waiting for {self.club.name} - {self.date} {self.start_time}"