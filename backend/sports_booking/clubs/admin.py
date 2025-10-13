from django.contrib import admin
from .models import SportsClub, TimeSlot, ClubReview

# Register your models here.
@admin.register(SportsClub)
class SportsClubAdmin(admin.ModelAdmin):
    list_display = ['id','name', 'rating', 'price_per_hour', 'is_active', 'created_at']
    list_filter = ['is_active', 'sports_available', 'rating', 'created_at']
    search_fields = ['name', 'address', 'description']
    readonly_fields = ['rating', 'total_reviews', 'created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Location', {
            'fields': ('address', 'latitude', 'longitude')
        }),
        ('Contact', {
            'fields':('contact_number', 'email')
        }),
        ('Sports & Pricing', {
            'fields': ('sports_available', 'price_per_hour', 'facilities', 'amenities')
        }),
        ('Operating Hours', {
            'fields': ('opening_time', 'closing_time', 'advance_booking_days')
        }),
        ('Media', {
            'fields': ('images',)
        }),
        ('Reviews', {
            'fields': ('rating', 'total_reviews'),
            'classes': ('collapse',)
        }),
        ('Policies', {
            'fields': ('cancellation_policy',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['club', 'date', 'start_time', 'end_time', 'sport', 'is_available', 'current_bookings', 'max_capacity']
    list_filter = ['is_available', 'sport', 'date', 'club']
    search_fields = ['club__name']
    date_hierarchy = 'date'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('club')

@admin.register(ClubReview)
class ClubReviewAdmin(admin.ModelAdmin):
    list_display = ['club', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['club__name', 'user__phone_number']
    readonly_fields = ['created_at']
    