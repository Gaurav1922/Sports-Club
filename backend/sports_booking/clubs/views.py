from rest_framework import viewsets, serializers as drf_serializers, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from django.db.models import Avg
import logging

from .models import Club, Sport, Review
from .serializers import ClubSerializer, ReviewSerializer, SportSerializer

logger = logging.getLogger(__name__)


class ClubViewSet(viewsets.ReadOnlyModelViewSet):
    """List and retrieve clubs"""
    serializer_class = ClubSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Club.objects.filter(
            is_active=True
        ).prefetch_related('sports').order_by('name')


class ReviewViewSet(viewsets.ModelViewSet):
    """CRUD for club reviews"""
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        club_id = self.kwargs.get('club_pk') or self.request.query_params.get('club')
        if club_id:
            return Review.objects.filter(club_id=club_id).select_related('user')
        return Review.objects.filter(
            club__reviews__isnull=False
        ).select_related('user').order_by('-created_at')

    def perform_create(self, serializer):
        club_id = self.request.data.get('club')
        serializer.save(user=self.request.user, club_id=club_id)


class SportViewSet(viewsets.ModelViewSet):
    """
    CRUD for sports under a specific club.
    GET    /api/clubs/<club_id>/sports/          — list (authenticated)
    POST   /api/clubs/<club_id>/sports/          — create (admin only)
    PATCH  /api/clubs/<club_id>/sports/<pk>/     — update (admin only)
    DELETE /api/clubs/<club_id>/sports/<pk>/     — delete (admin only)
    """
    serializer_class = SportSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def get_queryset(self):
        club_id = self.kwargs.get('club_id')
        return Sport.objects.filter(club_id=club_id).order_by('name')

    def perform_create(self, serializer):
        club_id = self.kwargs.get('club_id')
        try:
            club = Club.objects.get(id=club_id)
        except Club.DoesNotExist:
            raise drf_serializers.ValidationError({'error': 'Club not found'})
        serializer.save(club=club)