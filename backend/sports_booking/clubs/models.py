from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from phonenumber_field.modelfields import PhoneNumberField
from django.utils import timezone
from datetime import date, timedelta


# Create your models here.
class SportsClub(models.Model):
    SPORT_CHOICES = [
        ('football', 'Football'),
        ('basketball', 'Basketball'),
        ('tennis', 'Tennis'),
        ('badminton', 'Badminton'),
        ('swimming', 'Swimming'),
        ('cricket', 'Cricket'),
        ('volleyball', 'Volleyball'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    address = models.TextField()
    latitude = models.FloatField(validators=[MinValueValidator(-90), MaxValueValidator(90)])
    longitude = models.FloatField(validators=[MinValueValidator(-180), MaxValueValidator(180)])
    sports_available = models.JSONField(default=list)
    contact_number = PhoneNumberField(region='IN')
    email = models.EmailField()
    rating = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    images = models.JSONField(default=list) # store image urls
    price_per_hour = models.DecimalField(max_digits=8, decimal_places=2)
    facilities = models.JSONField(default=list)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Additional fields
    total_reviews = models.IntegerField(default=0)
    amenities = models.JSONField(default=list)
    cancellation_policy = models.TextField(blank=True)
    advance_booking_days = models.IntegerField(default=7)

    class Meta:
        db_table = 'clubs_sportsclub'
        ordering = ['-rating', 'name']

    def __str__(self):
        return self.name
    
    def update_rating(self):
        # Update average rating based on reviews
        from django.db.models import Avg
        avg_rating = self.reviews.aggregate(Avg('rating'))['rating__avg']
        if avg_rating:
            self.rating = round(avg_rating, 1)
            self.total_reviews = self.reviews.count()
            self.save(update_fields=['rating', 'total_reviews'])

class TimeSlot(models.Model):
    club = models.ForeignKey(SportsClub, on_delete=models.CASCADE, related_name='time_slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    sport = models.CharField(max_length=50, choices=SportsClub.SPORT_CHOICES)
    max_capacity = models.IntegerField(default=1)
    current_bookings = models.IntegerField(default=0)
    price_override = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'clubs_timeslot'
        unique_together = ['club', 'date', 'start_time', 'sport']
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.club.name} - {self.date} {self.start_time}-{self.end_time} ({self.sport})"
    
    @property
    def is_bookable(self):
        return(
            self.is_available and 
            self.current_bookings < self.max_capacity and
            self.date >= date.today()
        )
    
    @property
    def price(self):
        return self.price_override or self.club.price_per_hour

class ClubReview(models.Model):
    club = models.ForeignKey(SportsClub, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'clubs_clubreview'
        unique_together = ['club', 'user']
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.club.update_rating()
        
    