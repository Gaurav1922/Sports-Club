from django.contrib import admin
from .models import Payment

# Register your models here.

@admin.register(Payment)
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
        return super().has_delete_permission(request, obj)