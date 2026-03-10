from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookingViewSet

router = DefaultRouter()
router.register(r'', BookingViewSet, basename='booking')

urlpatterns = [
    path('', include(router.urls)),
]

"""from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from bookings.views import BookingViewSet
from clubs.views import ClubViewSet, SportViewSet, ReviewViewSet

# Create router for ViewSets
router = DefaultRouter()
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'clubs', ClubViewSet, basename='club')
router.register(r'sports', SportViewSet, basename='sport')
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API routes
    path('api/', include(router.urls)),
    path('api/accounts/', include('accounts.urls')),
    path('api/payments/', include('payments.urls')),
    
    # JWT token refresh
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
"""

