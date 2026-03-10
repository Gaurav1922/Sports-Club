from rest_framework import serializers
from .models import Payment
from django.utils import timezone
import uuid
from bookings.serializers import BookingSerializer

class PaymentSerializer(serializers.ModelSerializer):
    
    booking_id = serializers.IntegerField(source='booking.id', read_only=True)
    booking_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = [
            'id', 'booking', 'booking_id', 'booking_details', 
            'stripe_payment_intent_id', 'amount', 'currency', 'status', 
            'payment_method', 'created_at', 'completed_at', 'metadata']
        read_only_fields = ['created_at', 'completed_at', 'stripe_payment_intent_id']
    
    def get_booking_details(self, obj):
        return {
            'id': obj.booking.id,
            'club': obj.booking.club.name,
            'sport': obj.booking.sport.name,
            'date': obj.booking.date,
            'time': f"{obj.booking.start_time} - {obj.booking.end_time}"
        }

class PaymentIntentSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField()
    
    def validate_booking_id(self, value):
        from bookings.models import Booking
        try:
            Booking.objects.get(id=value)
        except Booking.DoesNotExist:
            raise serializers.ValidationError("Booking not found")
        return value

class PaymentConfirmSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField()
    payment_intent_id = serializers.CharField()
    
    def validate_booking_id(self, value):
        from bookings.models import Booking
        try:
            Booking.objects.get(id=value)
        except Booking.DoesNotExist:
            raise serializers.ValidationError("Booking not found")
        return value
    
    def validate_payment_intent_id(self, value):
        if not value.startswith('pi_'):
            raise serializers.ValidationError("Invalid payment intent ID format")
        return value

"""class CreatePaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Payment
        fields = ['booking', 'payment_method']

    def create(self, validated_data):
        booking = validated_data['booking']
        payment_method = validated_data.get('payment_method', 'qr')

        payment = Payment.objects.create(
            booking=booking,
            amount=booking.total_amount,
            payment_method=payment_method,
            upi_id='sportsclub@upi'
        )

        # Generate QR code fro QR payment method
        if payment_method == 'qr':
            payment.generate_qr_code()
        
        return payment"""