from rest_framework import viewsets, status
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q, F
from django.utils import timezone
from geopy.distance import geodesic
from datetime import date, timedelta
from .models import SportsClub, TimeSlot, ClubReview
from .serializers import SportsClubSerializer, TimeSlotSerializer, SportsClubDetailsSerializer, ClubReviewSerializer
import logging

logger = logging.getLogger(__name__)

# Create your views here.
class SportClubViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]

    queryset = SportsClub.objects.filter(is_active=True)
    serializer_class = SportsClubSerializer

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SportsClubDetailsSerializer
        return SportsClubSerializer

    @action(detail=False, methods=['get'])
    def nearby(self, request):
        print(request.query_params)

        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = request.query_params.get('radius')  # Default 10km
        sport = request.query_params.get('sport')

        if lat is None or lng is None: 

            return Response({'error': 'Latitude and longitude required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            lat = float(lat)
            lng = float(lng)
            radius = float(radius) if radius else 10.0  # default 10 km
        except ValueError:
            return Response({'error' 'Invalid coordinates or radius'}, status=status.HTTP_400_BAD_REQUEST)
        user_location = (lat, lng)
        clubs_with_distance = []

        queryset = self.get_queryset()
        if sport:
            queryset = queryset.filter(sports_available__contains=[sport])
            
        for club in queryset:
            club_location = (club.latitude, club.longitude)
            distance = geodesic(user_location, club_location).kilometers

            if distance <= radius:
                clubs_with_distance.append({
                    'club': club,
                    'distance': round(distance, 2)
                })
        
        # Sort by distance
        clubs_with_distance.sort(key=lambda x: x['distance'])

        # add user location to request for serializer
        request.user_location = user_location

        serializer = self.get_serializer(
            [item['club'] for item in clubs_with_distance],
            many=True,
            context={'request': request}
        )

        return Response(serializer.data)
        
    
    @action(detail=True, methods=['get'])
    def available_slots(self, request, pk=None):
        club = self.get_object()
        date_param = request.query_params.get('date')
        sport = request.query_params.get('sport')

        if not date_param:
            date_param = timezone.now().date()
        else:
            try:
                date_param = timezone.datetime.strptime(date_param, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    'error': 'Invalid date format. Use YYYY-MM-DD'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Don't allow booking past dates
        if date_param < timezone.now().date():
            return Response({
                'error': 'Cannot book slots for past dates'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        filters = {
            'club': club,
            'date': date_param,
            'is_available': True,
            'current_bookings__lt': F('max_capacity')
        }

        if sport:
            filters['sport'] = sport
        
        slots = TimeSlot.objects.filter(**filters).order_by('start_time')
        serializer = TimeSlotSerializer(slots, many=True)

        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_review(self, request, pk=None):
        club = self.get_object()

        # Check if user has booked this club before
        user_bookings = request.user.bookings.filter(
            club=club,
            status='completed'
        ).exists()

        if not user_bookings:
            return Response({
                'error': 'You can only review clubs you have booked'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ClubReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(club=club, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        sport = request.query_params.get('sport')
        min_rating = request.query_params.get('min_rating')
        max_price = request.query_params.get('max_price')

        queryset = self.get_queryset()

        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(address__icontains=query) |
                Q(description__icontains=query)
            )
        
        if sport:
            queryset = queryset.filter(sport_available__contains=[sport])
        
        if min_rating:
            try:
                queryset = queryset.filter(rating__gte=float(min_rating))
            except ValueError:
                pass
        
        if max_price:
            try:
                queryset = queryset.filter(price_per_hour__lte=float(max_price))
            except ValueError:
                pass
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    