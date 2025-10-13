from rest_framework import serializers
from .models import SportsClub, TimeSlot, ClubReview
from geopy.distance import geodesic
from django.utils import timezone
from django.db.models import F

class TimeSlotSerializer(serializers.ModelSerializer):
    is_bookable = serializers.ReadOnlyField()
    price = serializers.ReadOnlyField()
    
    class Meta:
        model = TimeSlot
        fields = '__all__'

class ClubReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.first_name', read_only=True)

    class Meta:
        model = ClubReview
        fields = ['id', 'rating', 'comment', 'created_at', 'user_name']
        read_only_fields = ['id', 'created_at', 'user_name']

class SportsClubSerializer(serializers.ModelSerializer):
    distance = serializers.SerializerMethodField()
    available_slots_today = serializers.SerializerMethodField()
    recent_reviews = ClubReviewSerializer(many=True, read_only=True, source='reviews')

    class Meta:
        model = SportsClub
        fields = '__all__'

    def get_distance(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user_location'):
            user_lat, user_lng = request.user_location
            club_location = (obj.latitude, obj.longitude)
            return round(geodesic((user_lat, user_lng), club_location).kilometers, 2)
        return None
    
    def get_available_slots_today(self, obj):
        today = timezone.now().date()
        return obj.time_slots.filter(
            date=today,
            is_available=True,
            current_bookings__lt=F('max_capacity')
        ).count()
    
class SportsClubDetailsSerializer(SportsClubSerializer):
    time_slots = TimeSlotSerializer(many=True, read_only=True)
    reviews = ClubReviewSerializer(many=True, read_only=True)

    class Meta(SportsClubSerializer.Meta):
        pass
    

