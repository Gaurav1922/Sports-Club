from rest_framework import serializers
from .models import Booking, SlotLock, SlotWaitlist

class SlotLockSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source='club.name', read_only=True)
    sport_name = serializers.CharField(source='sport.name', read_only=True)
    
    class Meta:
        model = SlotLock
        fields = ['id', 'club', 'club_name', 'sport', 'sport_name', 'date', 'start_time', 'end_time', 'locked_at', 'expires_at', 'is_converted']
        read_only_fields = ['locked_at', 'expires_at', 'is_converted']


class BookingSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source='club.name', read_only=True)
    sport_name = serializers.CharField(source='sport.name', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    has_review = serializers.SerializerMethodField()
    club_id = serializers.IntegerField(source='club.id', read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'user', 'user_name', 'user_email', 'club', 'club_id', 'club_name', 'sport', 'sport_name', 'date', 'start_time', 'end_time', 'amount', 'status', 'has_review', 'created_at', 'updated_at']
        read_only_fields = ['user', 'status', 'created_at', 'updated_at']
    
    def get_has_review(self, obj):
        from clubs.models import Review
        return Review.objects.filter(booking=obj).exists()
    
    
class BookingCreateSerializer(serializers.Serializer):
    club = serializers.IntegerField()
    sport = serializers.IntegerField()
    date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    lock_id = serializers.IntegerField()
    
class SlotWaitlistSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source='club.name', read_only=True)
    sport_name = serializers.CharField(source='sport.name', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    
    class Meta:
        model = SlotWaitlist
        fields = ['id', 'user', 'user_name', 'club', 'club_name', 'sport', 'sport_name', 'date', 'start_time', 'end_time', 'notified', 'created_at']
        read_only_fields = ['user', 'notified', 'created_at']
