from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SportClubViewSet

router = DefaultRouter()
router.register(r'', SportClubViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
