from django.contrib import admin
from .models import Payment
from django.utils.html import format_html

# Register your models here.

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'booking_link', 'user_link', 'amount', 'currency', 'status', 'payment_method', 'created_at', 'completed_at']
    list_filter = ['status', 'currency', 'payment_method', 'created_at']
    search_fields = ['booking__id', 'booking__user__username', 'booking__user__email', 'stripe_payment_intent_id']
    readonly_fields = ['created_at', 'completed_at', 'stripe_payment_intent_id', 'stripe_link', 'booking_details']
    date_hierarchy = 'created_at'
    list_per_page = 50
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('booking', 'booking_details', 'stripe_payment_intent_id', 'stripe_link')
        }),
        ('Amount & Currency', {
            'fields': ('amount', 'currency', 'payment_method')
        }),
        ('Status', {
            'fields': ('status', 'metadata')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'booking', 
            'booking__user', 
            'booking__club', 
            'booking__sport'
        )
    
    def booking_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        url = reverse('admin:bookings_booking_change', args=[obj.booking.id])
        return format_html('<a href="{}">{}</a>', url, f"Booking #{obj.booking.id}")
    booking_link.short_description = 'Booking'
    
    def user_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        url = reverse('admin:accounts_user_change', args=[obj.booking.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.booking.user.username)
    user_link.short_description = 'User'
    
    def stripe_link(self, obj):
        if obj.stripe_payment_intent_id:
            url = f"https://dashboard.stripe.com/payments/{obj.stripe_payment_intent_id}"
            return format_html('<a href="{}" target="_blank">View in Stripe →</a>', url)
        return "-"
    stripe_link.short_description = 'Stripe Dashboard'
    
    def booking_details(self, obj):
        return format_html(
            '<strong>{}</strong><br>'
            'Sport: {}<br>'
            'Date: {}<br>'
            'Time: {} - {}',
            obj.booking.club.name,
            obj.booking.sport.name,
            obj.booking.date,
            obj.booking.start_time,
            obj.booking.end_time
        )
    booking_details.short_description = 'Booking Details'
    
    actions = ['mark_as_completed', 'mark_as_failed']
    
    def mark_as_completed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='completed', completed_at=timezone.now())
        self.message_user(request, f'{updated} payments marked as completed.')
    mark_as_completed.short_description = 'Mark as completed'
    
    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} payments marked as failed.')
    mark_as_failed.short_description = 'Mark as failed'
    
"""@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_id', 'booking', 'amount', 'payment_method', 'status', 'created_at', 'is_locked', 'attempts'
    ]
    list_filter = ['status', 'payment_method', 'created_at', 'is_locked']
    search_fields = ['transaction_id', 'booking__user__phone_number','booking_id']
    readonly_fields = [
        'id','transaction_id', 'created_at', 'qr_code_hash', 'security_token', 'completed_at'
    ]
    
    fieldsets = (
        (None, {
            'fields': ('id','booking', 'transaction_id', 'amount')
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'status', 'upi_id')
        }),
        ('Security', {
            'fields': ('is_locked', 'attempts', 'last_attempt_at', 'qr_code_hash', 'security_token')
        }),
        ('QR Code', {
            'fields': ('qr_code', 'expires_at')
        }),
        ('Admin', {
            'fields': ('admin_notes', 'created_by_admin'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'booking', 'booking__user', 'booking__club'
        )
    
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of completed payments
        if obj and obj.status == 'completed':
            return False
        return super().has_delete_permission(request, obj)"""