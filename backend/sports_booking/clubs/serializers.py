from rest_framework import serializers
from .models import Club, Sport, Review


class SportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sport
        fields = ['id', 'name', 'price_per_hour', 'description', 'is_active']


class ClubSerializer(serializers.ModelSerializer):
    sports = SportSerializer(many=True, read_only=True)

    class Meta:
        model = Club
        fields = [
            'id', 'name', 'location', 'phone_number', 'opening_time',
            'closing_time', 'description', 'is_active', 'sports'
        ]

    def validate_phone_number(self, value):
        if value and not value.isdigit():
            raise serializers.ValidationError("Phone number must contain only digits")
        if value and len(value) != 10:
            raise serializers.ValidationError("Phone number must be exactly 10 digits")
        return value


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'user', 'user_name', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username