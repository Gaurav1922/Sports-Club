from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, OTP

# Register your models here.
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'mobile_number', 'full_name_display', 
                    'is_mobile_verified', 'is_staff', 'is_active', 'date_joined']
    list_filter = ['is_staff', 'is_active', 'is_mobile_verified', 'date_joined']
    search_fields = ['username', 'email', 'mobile_number', 'first_name', 'last_name']
    ordering = ['-date_joined']
    readonly_fields = ['date_joined', 'last_login', 'total_bookings']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('mobile_number', 'is_mobile_verified', 'total_bookings')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('mobile_number', 'email', 'first_name', 'last_name')
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('bookings')
    
    def full_name_display(self, obj):
        return obj.get_full_name() or '-'
    full_name_display.short_description = 'Full Name'

    def total_bookings(self, obj):
        count = obj.bookings.count()
        if count > 0:
            url = f"/admin/bookings/booking/?user__id__exact={obj.id}"
            return format_html('<a href="{}">{} bookings</a>', url, count)
        return '0 bookings'
    total_bookings.short_description = 'Total Bookings'

    actions = ['activate_users', 'deactivated_users', 'verify_mobile']

    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users activated.')
    activate_users.short_description = 'Activate selected users'

    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} user deactivated.')
    deactivate_users.short_description = 'Deactivate selected users'

    def verify_mobile(self, request, queryset):
        updated = queryset.update(is_mobile_verified=True)
        self.message_user(request, f'{updated} users verified.')
    verify_mobile.short_description = 'Mark mobile as verified'

@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ['mobile_number', 'otp', 'created_at', 'expires_at', 
                    'is_verified', 'is_expired_display', 'ip_address']
    list_filter = ['is_verified', 'created_at', 'expires_at']
    search_fields = ['mobile_number', 'otp', 'ip_address']
    readonly_fields = ['created_at', 'is_expired_display']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    list_per_page = 100
    
    fieldsets = (
        ('OTP Information', {
            'fields': ('mobile_number', 'otp', 'is_verified')
        }),
        ('Validity', {
            'fields': ('created_at', 'expires_at', 'is_expired_display')
        }),
        ('Tracking', {
            'fields': ('ip_address',),
            'classes': ('collapse',)
        }),
    )

    def is_expired_display(self, obj):
        from django.utils import timezone
        if timezone.now() > obj.expires_at:
            return format_html('<span style="color: red;">❌ Expired</span>')
        return format_html('<span style="color: green;">✅ Valid</span>')
    is_expired_display.short_description = 'Status'
    
    actions = ['delete_expired_otps', 'mark_as_verified', 'delete_unverified_old']
    
    def delete_expired_otps(self, request, queryset):
        from django.utils import timezone
        expired = queryset.filter(expires_at__lt=timezone.now())
        count = expired.count()
        expired.delete()
        self.message_user(request, f'{count} expired OTPs deleted.')
    delete_expired_otps.short_description = 'Delete expired OTPs'
    
    def mark_as_verified(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} OTPs marked as verified.')
    mark_as_verified.short_description = 'Mark as verified'
    
    def delete_unverified_old(self, request, queryset):
        from django.utils import timezone
        from datetime import timedelta
        old_date = timezone.now() - timedelta(days=1)
        old_unverified = queryset.filter(
            is_verified=False,
            created_at__lt=old_date
        )
        count = old_unverified.count()
        old_unverified.delete()
        self.message_user(request, f'{count} old unverified OTPs deleted.')
    delete_unverified_old.short_description = 'Delete old unverified OTPs'
    