from rest_framework import viewsets, serializers as drf_serializers, permissions
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.exceptions import ValidationError
import logging

from .models import Club, Sport, Review
from .serializers import ClubSerializer, ReviewSerializer, SportSerializer

logger = logging.getLogger(__name__)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission: safe methods (GET/HEAD/OPTIONS) are open to any
    authenticated user; PATCH/PUT/DELETE are only allowed for the review's
    own author. This was completely missing before, allowing any logged-in
    user to edit or delete anyone else's review (IDOR).
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user_id == request.user.id


class ClubViewSet(viewsets.ReadOnlyModelViewSet):
    """List and retrieve clubs"""
    serializer_class = ClubSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # prefetch_related('reviews') added alongside 'sports' — without it,
        # every club in a list response triggered 2 extra queries
        # (average_rating + total_reviews), i.e. an N+1 on the busiest
        # read endpoint in the app.
        return Club.objects.filter(
            is_active=True
        ).prefetch_related('sports', 'reviews').order_by('name')


class ReviewViewSet(viewsets.ModelViewSet):
    """CRUD for club reviews"""
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        club_id = self.kwargs.get('club_pk') or self.request.query_params.get('club')
        if club_id:
            return Review.objects.filter(club_id=club_id).select_related('user')
        return Review.objects.select_related('user').order_by('-created_at')

    def perform_create(self, serializer):
        club_id = self.request.data.get('club')
        if not club_id:
            raise ValidationError({'club': 'Club ID is required'})

        if not Club.objects.filter(id=club_id, is_active=True).exists():
            raise ValidationError({'club': 'Club not found'})

        if Review.objects.filter(club_id=club_id, user=self.request.user).exists():
            raise ValidationError({'detail': 'You have already reviewed this club'})

        # Require a real, completed transaction before a review can be left —
        # previously anyone could review a club they never booked.
        from bookings.models import Booking
        qualifying_booking = Booking.objects.filter(
            user=self.request.user, club_id=club_id,
            status__in=['confirmed', 'completed']
        ).order_by('-date').first()

        if not qualifying_booking:
            raise ValidationError(
                {'detail': 'You can only review a club after booking with them.'}
            )

        serializer.save(user=self.request.user, club_id=club_id, booking=qualifying_booking)


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