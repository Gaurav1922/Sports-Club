from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, OTP

# Register your models here.
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('phone_number', 'first_name', 'last_name', 'is_phone_verified', 'is_active', 'date_joined')
    list_filter = ('is_phone_verified', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('phone_number', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {"fields": ('phone_number', 'password'),}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields':('last_login', 'date_joined')}),
        ('Security', {'fields': ('is_phone_verified', 'failed_login_attempts', 'is_locked')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'password1', 'password2'),
        }),
    )

@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'otp', 'created_at', 'is_verified', 'attempts')
    list_filter = ('is_verified', 'created_at')
    search_fields = ['phone_number']
    readonly_fields = ('otp', 'created_at')
    
    