from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import Payment


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
        url = reverse('admin:bookings_booking_change', args=[obj.booking.id])
        return format_html('<a href="{}">{}</a>', url, f"Booking #{obj.booking.id}")
    booking_link.short_description = 'Booking'

    def user_link(self, obj):
        from django.urls import reverse
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
        updated = 0
        for payment in queryset.select_related('booking'):
            payment.status = 'completed'
            payment.completed_at = timezone.now()
            payment.save(update_fields=['status', 'completed_at'])
            if payment.booking.status != 'confirmed':
                payment.booking.status = 'confirmed'
                payment.booking.save(update_fields=['status', 'updated_at'])
            updated += 1
        self.message_user(request, f'{updated} payment(s) marked as completed and bookings confirmed.')
    mark_as_completed.short_description = 'Mark as completed (also confirms booking)'

    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='failed', failed_at=timezone.now())
        self.message_user(request, f'{updated} payments marked as failed.')
    mark_as_failed.short_description = 'Mark as failed'