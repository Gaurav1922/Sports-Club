from django.urls import path
from . import views
from django.http import JsonResponse
from django.utils import timezone


def health_check(request):
    """Lightweight health check — keeps server warm"""
    return JsonResponse({'status': 'ok', 'time': str(timezone.now())})


urlpatterns = [
    # Health check — used by UptimeRobot / keep-alive pings
    path('health/', health_check, name='health_check'),

    # NOTE: the old setup/, reset-admin/, and flush-setup/ endpoints have
    # been removed — they allowed anyone with the (publicly-visible) key to
    # wipe the production database and create/reset a superuser with no
    # authentication. Use `python manage.py create_admin` instead (run it
    # from Render's shell, or as a one-off release command), with
    # ADMIN_USERNAME / ADMIN_PASSWORD / ADMIN_EMAIL / ADMIN_MOBILE set as
    # env vars.

    # Authentication endpoints
    path('send-otp/', views.SendOTPView.as_view(), name='send_otp'),
    path('verify-otp/', views.VerifyOTPView.as_view(), name='verify_otp'),
    path('register/', views.RegisterView.as_view(), name='register'),

    # Profile endpoints
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),

    # Admin — stats & bookings
    path('admin/dashboard-stats/', views.dashboard_stats, name='dashboard_stats'),
    path('admin/monthly-report/', views.monthly_report, name='monthly_report'),
    path('admin/bookings/', views.all_bookings, name='admin_all_bookings'),
    path('admin/bookings/<int:booking_id>/status/', views.update_booking_status, name='update_booking_status'),
    path('admin/users/', views.all_users, name='admin_all_users'),
    path('admin-login/', views.admin_login, name='admin_login'),

    # Admin clubs endpoints
    path('admin/clubs/', views.admin_clubs, name='admin_clubs'),
    path('admin/clubs/<int:club_id>/', views.admin_club_detail, name='admin_club_detail'),
]