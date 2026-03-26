from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClubViewSet, ReviewViewSet, SportViewSet

router = DefaultRouter()
router.register(r'', ClubViewSet, basename='club')

urlpatterns = [
    path('', include(router.urls)),
    # Reviews — explicit POST allowed
    path('reviews/', ReviewViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='reviews-list'),
    path('reviews/<int:pk>/', ReviewViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='reviews-detail'),
    # Sports under a club
    path('<int:club_id>/sports/', SportViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('<int:club_id>/sports/<int:pk>/', SportViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'})),
]
