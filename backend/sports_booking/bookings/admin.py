from django.contrib import admin
from .models import Booking, SlotWaitlist, SlotLock

# Register your models here.

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
   class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'club', 'sport', 'date', 'start_time', 'status', 'amount', 'created_at']
    list_filter = ['status', 'date', 'created_at', 'club']
    search_fields = ['user__username', 'user__email', 'club__name', 'sport__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
    list_per_page = 50
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('user', 'club', 'sport', 'date', 'start_time', 'end_time')
        }),
        ('Payment & Status', {
            'fields': ('amount', 'status', 'lock')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'club', 'sport', 'lock'
        )

    actions = ['mark_confirmed', 'mark_cancelled', 'mark_completed']

    def mark_confirmed(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f'{updated} bookings marked as confirmed.')
    mark_confirmed.short_description = 'Mark selected bookings as confirmed'
    
    def mark_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} bookings marked as cancelled.')
    mark_cancelled.short_description = 'Mark selected bookings as cancelled'
    
    def mark_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} bookings marked as completed.')
    mark_completed.short_description = 'Mark selected bookings as completed'
    
@admin.register(SlotLock)
class SlotLockAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'club', 'sport', 'date', 'start_time', 'locked_at', 'expires_at', 'is_converted', 'is_expired_display']
    list_filter = ['is_converted', 'date', 'locked_at', 'club']
    search_fields = ['user__username', 'user__email', 'club__name', 'sport__name']
    readonly_fields = ['locked_at', 'expires_at', 'is_expired_display']
    date_hierarchy = 'date'
    list_per_page = 50
    
    fieldsets = (
        ('Lock Information', {
            'fields': ('user', 'club', 'sport', 'date', 'start_time', 'end_time')
        }),
        ('Lock Status', {
            'fields': ('locked_at', 'expires_at', 'is_converted', 'is_expired_display')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'club', 'sport')
    
    def is_expired_display(self, obj):
        from django.utils import timezone
        expired = timezone.now() > obj.expires_at
        if expired:
            return '❌ Expired'
        return '✅ Active'
    is_expired_display.short_description = 'Status'
    
    actions = ['delete_expired_locks']
    
    def delete_expired_locks(self, request, queryset):
        from django.utils import timezone
        expired = queryset.filter(expires_at__lt=timezone.now(), is_converted=False)
        count = expired.count()
        expired.delete()
        self.message_user(request, f'{count} expired locks deleted.')
    delete_expired_locks.short_description = 'Delete expired locks'

@admin.register(SlotWaitlist)
class SlotWaitlistAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'club', 'sport', 'date', 'start_time', 'notified', 'created_at']
    list_filter = ['notified', 'date', 'created_at']
    search_fields = ['user__username', 'club__name', 'sport__name']
    readonly_fields = ['created_at']
    date_hierarchy = 'date'
    list_per_page = 50
    
    fieldsets = (
        ('Waitlist Information', {
            'fields': ('user', 'club', 'sport', 'date', 'start_time', 'end_time')
        }),
        ('Notification Status', {
            'fields': ('notified', 'created_at')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'club', 'sport')
    
    def get_status(self, obj):
        if obj.notified:
            return '✅ Notified'
        return '⏳ Waiting'
    get_status.short_description = 'Status'
    
    actions = ['mark_as_notified', 'send_notification_now']
    
    def mark_as_notified(self, request, queryset):
        updated = queryset.update(notified=True)
        self.message_user(request, f'{updated} entries marked as notified.')
    mark_as_notified.short_description = 'Mark as notified'
    
    def send_notification_now(self, request, queryset):
        from .tasks import notify_waitlisted_users
        count = 0
        for entry in queryset.filter(notified=False):
            notify_waitlisted_users.delay(
                entry.club.id,
                entry.sport.id,
                entry.date.strftime('%Y-%m-%d'),
                str(entry.start_time),
                str(entry.end_time)
            )
            count += 1
        self.message_user(request, f'Notification queued for {count} entries.')
    send_notification_now.short_description = 'Send notification now'