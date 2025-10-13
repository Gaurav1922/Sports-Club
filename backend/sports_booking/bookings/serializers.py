from rest_framework import serializers
from .models import Booking
from clubs.serializers import SportsClubSerializer, TimeSlotSerializer

class BookingSerializer(serializers.ModelSerializer):
    club = SportsClubSerializer(read_only=True)
    time_slot = TimeSlotSerializer(read_only = True)
    can_cancel = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ['id', 'user', 'booking_date', 'total_amount']
    
    def get_can_cancel(self, obj):
        can_cancel, message = obj.can_cancel()
        return {'allowed': can_cancel, 'reason': message}

class CreateBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['club', 'time_slot', 'special_requests']

    def validate(self,attrs):

        
        club = attrs['club']
        time_slot = attrs['time_slot']

        """print("Validating booking:", data)
        return data"""

        # Validate that time slot belongs to the club
        if time_slot.club != club:
            raise serializers.ValidationError("Time slot does not belong to the selected club")
        
        
        
        # validate that time time slot is available
        if not time_slot.is_bookable:
            raise serializers.ValidationError("Selected time slot is not available")
        
        return attrs

       

        