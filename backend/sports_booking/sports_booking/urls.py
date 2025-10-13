
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from django.http import JsonResponse
from django.utils import timezone


def api_root(request):
    return JsonResponse({
        'message': 'Sports Club Booking API',
        'version': '1.0',
        'endpoints': {
            'auth': '/api/auth/',
            'clubs': '/api/clubs/',
            'bookings': '/api/bookings/',
            'payments': '/api/payments/',
        }
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api_root, name='api_root'),
    path('api/auth/', include('accounts.urls')),
    path('api/clubs/', include('clubs.urls')),
    path('api/bookings/', include('bookings.urls')),
    path('api/payments/', include('payments.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Add health check endpoint
def health_check(request):
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat()
    })

urlpatterns += [
    path('health/', health_check, name='health_check'),
]