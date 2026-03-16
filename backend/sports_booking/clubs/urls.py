from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClubViewSet, ReviewViewSet, SportViewSet

router = DefaultRouter()
router.register(r'', ClubViewSet, basename='club')
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = [
    path('', include(router.urls)),
    # Nested sports endpoints: /api/clubs/<club_id>/sports/
    path('<int:club_id>/sports/', SportViewSet.as_view({'get': 'list', 'post': 'create'}), name='club-sports'),
    path('<int:club_id>/sports/<int:pk>/', SportViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='club-sport-detail'),
]