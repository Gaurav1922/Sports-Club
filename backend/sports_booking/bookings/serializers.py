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
        """
        Reads the payment method off the already-fetched `payment` relation.
        The view MUST select_related('payment') so this never issues its own query.
        Falls back to a direct query only if the relation wasn't preloaded
        (e.g. this serializer is reused somewhere without select_related).
        """
        try:
            payment = obj.payment
        except Booking.payment.RelatedObjectDoesNotExist:
            return None
        except AttributeError:
            # payment relation wasn't select_related'd — fall back safely
            payment = obj.__class__.objects.filter(pk=obj.pk).values(
                'payment__payment_method'
            ).first()
            return (payment or {}).get('payment__payment_method') or None

        method = (payment.payment_method or '').strip()
        return method if method else 'card'


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