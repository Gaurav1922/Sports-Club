from rest_framework import viewsets, status
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Q
from .models import Sport, Club, Review
from .serializers import ClubSerializer, SportSerializer, ReviewSerializer, ClubDetailSerializer
from bookings.models import Booking


# Create your views here.
class ClubViewSet(viewsets.ModelViewSet):
    queryset = Club.objects.filter(is_active=True).prefetch_related('sports')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ClubDetailSerializer
        return ClubSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Search functionality
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(location__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Filter by location
        location = self.request.query_params.get('location', None)
        if location:
            queryset = queryset.filter(location__icontains=location)
        
        # Filter by sport
        sport = self.request.query_params.get('sport', None)
        if sport:
            queryset = queryset.filter(sports__name__icontains=sport).distinct()
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Get reviews for a specific club"""
        club = self.get_object()
        reviews = club.reviews.select_related('user').all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def sports(self, request, pk=None):
        """Get sports for a specific club"""
        club = self.get_object()
        sports = club.sports.filter(is_active=True)
        serializer = SportSerializer(sports, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get popular clubs based on bookings"""
        from django.db.models import Count
        
        popular_clubs = Club.objects.filter(
            is_active=True
        ).annotate(
            booking_count=Count('bookings')
        ).order_by('-booking_count')[:10]
        
        serializer = self.get_serializer(popular_clubs, many=True)
        return Response(serializer.data)

class SportViewSet(viewsets.ModelViewSet):
    queryset = Sport.objects.filter(is_active=True)
    serializer_class = SportSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by club
        club = self.request.query_params.get('club', None)
        if club:
            queryset = queryset.filter(club_id=club)
        
        # Search by name
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Review.objects.all()
        return Review.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Create a review for a club"""
        club_id = request.data.get('club')
        
        if not club_id:
            return Response(
                {'error': 'club field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user has completed booking at this club
        has_booking = Booking.objects.filter(
            user=request.user,
            club_id=club_id,
            status='completed'
        ).exists()
        
        if not has_booking:
            return Response(
                {'error': 'You can only review clubs where you have completed a booking'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already reviewed
        existing_review = Review.objects.filter(
            user=request.user,
            club_id=club_id
        ).first()
        
        if existing_review:
            # Update existing review
            serializer = self.get_serializer(existing_review, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        # Create new review
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update user's own review"""
        review = self.get_object()
        
        # Check permission
        if review.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You can only edit your own reviews'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete user's own review"""
        review = self.get_object()
        
        # Check permission
        if review.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You can only delete your own reviews'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)