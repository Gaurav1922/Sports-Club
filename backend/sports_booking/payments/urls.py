from django.urls import path, include
from .views import PaymentViewSet, AdminPaymentViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'', PaymentViewSet, basename='payment')
router.register(r'admin', AdminPaymentViewSet, basename='admin-payment')


urlpatterns = [
    path('', include(router.urls)),
]


# Additional utility views for payment integration
