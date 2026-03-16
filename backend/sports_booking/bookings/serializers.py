from rest_framework import serializers
from .models import Booking, SlotLock, SlotWaitlist


class BookingSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source='club.name', read_only=True)
    club_location = serializers.CharField(source='club.location', read_only=True)
    club_phone = serializers.CharField(source='club.phone_number', read_only=True)
    sport_name = serializers.CharField(source='sport.name', read_only=True)
    user_name = serializers.SerializerMethodField()
    payment_method = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id', 'user', 'user_name', 'club', 'club_name', 'club_location',
            'club_phone', 'sport', 'sport_name',
            'date', 'start_time', 'end_time', 'amount', 'status',
            'payment_method', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_payment_method(self, obj):
        """Return payment method from related payment record"""
        try:
            from payments.models import Payment as PaymentModel
            p = PaymentModel.objects.filter(
                booking=obj, status='completed'
            ).values('payment_method').first()
            if p:
                method = (p['payment_method'] or '').strip()
                return method if method else 'card'
        except Exception:
            pass
        # Also check confirmed status (some may be confirmed without completed payment in dev)
        try:
            from payments.models import Payment as PaymentModel
            p = PaymentModel.objects.filter(booking=obj).values('payment_method', 'status').first()
            if p:
                method = (p['payment_method'] or '').strip()
                return method if method else 'card'
        except Exception:
            pass
        return None


class SlotLockSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlotLock
        fields = ['id', 'club', 'sport', 'date', 'start_time', 'end_time', 'expires_at', 'is_converted']
        read_only_fields = ['id', 'expires_at']


class SlotWaitlistSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source='club.name', read_only=True)
    sport_name = serializers.CharField(source='sport.name', read_only=True)

    class Meta:
        model = SlotWaitlist
        fields = [
            'id', 'club', 'club_name', 'sport', 'sport_name',
            'date', 'start_time', 'end_time', 'notified', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'notified']