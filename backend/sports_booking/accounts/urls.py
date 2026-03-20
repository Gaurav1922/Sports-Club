from django.urls import path
from . import views
from .views import create_admin
from django.http import JsonResponse
from django.utils import timezone

def health_check(request):
    """Lightweight health check — keeps server warm"""
    return JsonResponse({'status': 'ok', 'time': str(timezone.now())})

urlpatterns = [
    # Health check — used by UptimeRobot / keep-alive pings
    path('health/', health_check, name='health_check'),

    path('setup/', create_admin, name='create_admin'),
    path('reset-admin/', reset_admin, name='reset_admin'),


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

    # Admin clubs endpoints
    path('admin/clubs/', views.admin_clubs, name='admin_clubs'),
    path('admin/clubs/<int:club_id>/', views.admin_club_detail, name='admin_club_detail'),
]
