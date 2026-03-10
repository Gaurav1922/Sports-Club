from django.db import models
from django.utils import timezone

class Payment(models.Model):
    STATUS_CHOICES=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    booking = models.OneToOneField('bookings.Booking', on_delete=models.CASCADE, related_name='payment')
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stripe_payment_intent_id']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Payment for Booking #{self.booking.id} - {self.status}"
    
    def mark_completed(self):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()