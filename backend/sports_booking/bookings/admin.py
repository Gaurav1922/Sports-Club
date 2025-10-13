from django.contrib import admin
from .models import Booking

# Register your models here.

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'club', 'time_slot', 'status',
        'payment_status', 'total_amount', 'booking_date'
    ]
    list_filter = ['status', 'payment_status', 'booking_date', 'time_slot__date']
    search_fields = ['user__phone_number', 'club__name', 'id']
    readonly_fields = ['id', 'booking_date', 'total_amount']

    fieldsets = (
        (None, {
            'fields': ('id', 'user', 'club', 'time_slot')
        }),
        ('Status', {
            'fields': ('status', 'payment_status')
        }),
        ('Amount', {
            'fields': ('total_amount',)
        }),
        ('Additional Info', {
            'fields': ('special_requests', 'admin_notes')
        }),
        ('Cancellation', {
            'fields': ('cancelled_at', 'cancellation_reason'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('booking_date',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'club', 'time_slot'
        )