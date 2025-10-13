from django.db import models
from django.contrib.auth import get_user_model
from clubs.models import SportsClub, TimeSlot
import uuid

User = get_user_model()

# Create your models here.

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('no_show', 'No Show'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    club = models.ForeignKey(SportsClub, on_delete=models.CASCADE, related_name='bookings')
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name='bookings')
    booking_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    special_requests = models.TextField(blank=True)

    # Cancellation details
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)

    # Admin Fields
    admin_notes = models.TextField(blank=True)

    class Meta:
        db_table = 'bookings_booking'
        ordering = ['-booking_date']

    def __str__(self):
        return f"{self.user.phone_number} - {self.club.name} - {self.time_slot.date}"
    
    def can_cancel(self):
        # Check if booking can be cancelled
        from datetime import datetime, timedelta

        if self.status not in ['pending', 'confirmed']:
            return False, "Only pending or confirmed bookings can be cancelled"
        
        # Check if booking is more than 2 hours away
        slot_datetime = datetime.combine(self.time_slot.date, self.time_slot.start_time)
        current_time = datetime.now()

        if slot_datetime - current_time < timedelta(hours=2):
            return False, "Cannot cancel booking less than 2 hours before slot time"
        
        return True, "OK"
    
    def cancel_booking(self, reason=""):
        from django.utils import timezone
        # Cancel the booking and free up the slot
        can_cancel, message = self.can_cancel()
        if not can_cancel:
            raise ValueError(message)
        
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.cancellation_reason = reason
        self.save()

        # Free up the time slot
        self.time_slot.current_bookings = max(0, self.time_slot.current_bookings - 1)
        if self.time_slot.current_bookings < self.time_slot.max_capacity:
            self.time_slot.is_available = True
        self.time_slot.save()
