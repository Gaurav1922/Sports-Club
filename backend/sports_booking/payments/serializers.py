from rest_framework import serializers
from .models import Payment
from django.conf import settings


class PaymentSerializer(serializers.ModelSerializer):
    booking_id = serializers.CharField(source='booking.id', read_only=True)
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
            'id': str(obj.booking.id),
            'club': obj.booking.club.name,
            'sport': obj.booking.sport.name,
            'date': obj.booking.date,
            'time': f"{obj.booking.start_time} - {obj.booking.end_time}"
        }


class PaymentIntentSerializer(serializers.Serializer):
    booking_id = serializers.CharField()  # UUID as string


class PaymentConfirmSerializer(serializers.Serializer):
    booking_id = serializers.CharField()  # UUID as string
    payment_intent_id = serializers.CharField(max_length=200)
    payment_method = serializers.CharField(max_length=50, required=False, default='card')

    def validate_payment_intent_id(self, value):
        if settings.DEBUG:
            return value
        if not value.startswith('pi_'):
            raise serializers.ValidationError("Invalid payment intent ID format")
        return value