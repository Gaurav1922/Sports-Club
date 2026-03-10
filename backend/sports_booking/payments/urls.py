from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'payments', views.PaymentViewSet, basename='payment')

urlpatterns = [
    # Payment processing
    path('create-intent/', views.create_payment_intent, name='create_payment_intent'),
    path('confirm/', views.confirm_payment, name='confirm_payment'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
    
    # Admin actions
    path('refund/<int:payment_id>/', views.refund_payment, name='refund_payment'),
    
    # ViewSet routes
    path('', include(router.urls)),
]