from rest_framework import serializers
from .models import Club, Sport, Review


class SportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sport
        fields = ['id', 'name', 'price_per_hour', 'description', 'is_active']


class ClubSerializer(serializers.ModelSerializer):
    sports = SportSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()

    class Meta:
        model = Club
        fields = [
            'id', 'name', 'location', 'phone_number', 'opening_time',
            'closing_time', 'description', 'is_active', 'sports',
            'average_rating', 'total_reviews'
        ]

    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if not reviews:
            return None
        return round(sum(r.rating for r in reviews) / len(reviews), 1)

    def get_total_reviews(self, obj):
        return obj.reviews.count()

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
        fields = ['id', 'user', 'user_name', 'club', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username