from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError  # FIX 1: Import for clean()

User = get_user_model()


class Club(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=500)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    description = models.TextField(blank=True)
    phone_number = models.CharField(max_length=10, blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clubs'
        ordering = ['name']

    def __str__(self):
        return self.name

    # FIX 2: Added clean() to enforce opening < closing time at model level
    def clean(self):
        if self.opening_time and self.closing_time:
            if self.opening_time >= self.closing_time:
                raise ValidationError("Opening time must be before closing time")

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():  # FIX 3: Use .exists() instead of truthiness check on queryset
            total = sum(r.rating for r in reviews)
            return round(total / reviews.count(), 1)
        return None

    @property
    def total_reviews(self):
        return self.reviews.count()


class Sport(models.Model):
    name = models.CharField(max_length=100)
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='sports')
    price_per_hour = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]  # FIX 4: Price cannot be negative
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'sports'
        unique_together = ['name', 'club']

    def __str__(self):
        return f"{self.name} - {self.club.name}"


class Review(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    booking = models.OneToOneField(
        'bookings.Booking', on_delete=models.CASCADE, null=True, blank=True
    )
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']
        # FIX 5: Prevent duplicate reviews by same user for same club
        unique_together = ['club', 'user']
        indexes = [
            models.Index(fields=['club', 'user']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.club.name} - {self.rating}⭐"