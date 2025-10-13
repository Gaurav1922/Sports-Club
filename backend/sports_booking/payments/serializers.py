from rest_framework import serializers
from .models import Payment
from django.utils import timezone
import uuid
from bookings.serializers import BookingSerializer

class PaymentSerializer(serializers.ModelSerializer):
    
    booking_details = BookingSerializer(source='booking', read_only=True)
    time_remaining = serializers.SerializerMethodField()
    security_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = [
            'id', 'transaction_id', 'amount', 'payment_method', 'status',
            'expires_at', 'created_at', 'booking', 'booking_details',
            'time_remaining', 'security_status'
        ]
        read_only_fields = [
            'id', 'transaction_id', 'created_at', 'expires_at'
        ]
    
    """def get_booking_details(self, obj):
        from bookings.serializers import BookingSerializer
        return BookingSerializer(obj.booking).data"""
    
    def get_time_remaining(self, obj):
        if obj.is_expired():
            return 0
        
        remaining = obj.expires_at - timezone.now()
        return max(0, int(remaining.total_seconds()))
    
    def get_security_status(self, obj):
        return {
            'is_locked': obj.is_locked,
            'attempts_used': obj.attempts,
            'attempts_remaining': max(0, 5 - obj.attempts),
            'integrity_verified': obj.verify_qr_integrity() if obj.qr_code else None
        }

"""class PaymentSerializer(serializers.ModelSerializer):
    booking_details = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            'id', 'transaction_id', 'amount', 'payment_method', 'status', 'qr_code', 'upi_id', 'created_at', 'completed_at', 'booking', 'booking_details'
        ]
        read_only_fields = ['id', 'transaction_id', 'created_at', 'completed_at', 'qr_code']
    
    def get_booking_details(self, obj):
        from bookings.serializers import BookingSerializer
        return BookingSerializer(obj.booking).data"""

class CreatePaymentSerializer(serializers.ModelSerializer):

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
        
        return payment
    
"""class PaymentStatusSerializer(serializers.Serializer):
    transaction_id = serializers.CharField()
    status = serializers.ChoiceField(choices=Payment.STATUS_CHOICES)

    def validate_transaction_id(self,value):
        try:
            Payment.objects.get(transaction_id=value)
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Invalid transaction ID")
        return value

class RefundSerializer(serializers.Serializer):
    transaction_id = serializers.CharField()
    reason = serializers.CharField(required=False)

    def validate_transaction_id(self, value):
        try:
            payment = Payment.objects.get(transaction_id=value)
            if payment.status != 'completed':
                raise serializers.ValidationError("Can you refund completed payments")
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Invalid transaction ID")
        return value"""
    