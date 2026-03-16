from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator

class Payment(models.Model):
    STATUS_CHOICES=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    booking = models.OneToOneField(
        'bookings.Booking', on_delete=models.CASCADE, related_name='payment')
    
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)] # amount must be >= 0
    )
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)
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
        self.save(update_fields=['status', 'completed_at'])
        
    # Added mark_failed() - was missing, needed when stripe returns failure
    def mark_failed(self, reason=''):
        self.status = 'failed'
        self.failed_at = timezone.now()
        self.failure_reason = reason
        self.save(update_fields=['status', 'failed_at', 'failure_reason'])
    
    # added mark_refunded() - needed for cancellation/refund flow
    def mark_refunded(self):
        self.status = 'refunded'
        self.save(update_fields=['status'])