from django.urls import path
from .views import ClubViewSet, ReviewViewSet, SportViewSet

urlpatterns = [
    # Reviews — explicit paths, before clubs to avoid conflict
    path('reviews/', ReviewViewSet.as_view({'get': 'list', 'post': 'create'}), name='reviews-list'),
    path('reviews/<int:pk>/', ReviewViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='reviews-detail'),

    # Sports under a club
    path('<int:club_id>/sports/', SportViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('<int:club_id>/sports/<int:pk>/', SportViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'})),

    # Clubs — explicit paths last
    path('', ClubViewSet.as_view({'get': 'list'}), name='club-list'),
    path('<int:pk>/', ClubViewSet.as_view({'get': 'retrieve'}), name='club-detail'),
]
