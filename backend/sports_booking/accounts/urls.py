from django.urls import path
from . import views

urlpatterns = [
    # Authentication endpoints
    path('send-otp/', views.SendOTPView.as_view(), name='send_otp'),
    path('verify-otp/', views.VerifyOTPView.as_view(), name='verify_otp'),
    path('register/', views.RegisterView.as_view(), name='register'),
    
    # Profile endpoints
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    
    # Admin endpoints
    path('admin/dashboard-stats/', views.dashboard_stats, name='dashboard_stats'),
    path('admin/bookings/', views.all_bookings, name='admin_all_bookings'),
    path('admin/bookings/<int:booking_id>/status/', views.update_booking_status, name='update_booking_status'),
    path('admin/users/', views.all_users, name='admin_all_users'),
]