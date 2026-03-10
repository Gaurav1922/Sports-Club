from rest_framework import serializers
from .models import Sport, Club, Review

class SportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sport
        fields = ['id', 'name', 'price_per_hour', 'description', 'is_active']
        
    def validate_price_per_hour(self, value):
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative")
        return value
    
class ClubSerializer(serializers.ModelSerializer):
    sports = SportSerializer(many=True, read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    total_reviews = serializers.IntegerField(read_only=True)

    class Meta:
        model = Club
        fields = ['id', 'name', 'location',
                  'opening_time', 'closing_time', 
                  'description', 'sports', 'average_rating', 'total_reviews', 'created_at']
        read_only_fields = ['created_at']
        
    def validate(self, data):
        if 'opening_time' in data and 'closing_time' in data:
            if data['opening_time'] >= data['closing_time']:
                raise serializers.ValidationError(
                    "Opening time must be before closing time"
                )
        return data

class ClubDetailSerializer(serializers.ModelSerializer):
    sports = SportSerializer(many=True, read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    total_reviews = serializers.IntegerField(read_only=True)
    recent_reviews = serializers.SerializerMethodField()
    
    class Meta:
        model = Club
        fields = ['id', 'name', 'location', 'opening_time', 'closing_time', 
                  'description', 'is_active', 'sports', 'average_rating', 
                  'total_reviews', 'recent_reviews', 'created_at']
        read_only_fields = ['created_at']
    
    def get_recent_reviews(self, obj):
        recent = obj.reviews.select_related('user').order_by('-created_at')[:5]
        return ReviewSerializer(recent, many=True).data


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'club', 'user', 'user_name', 'rating', 'comment', 'created_at']
        read_only_fields = ['user', 'created_at', 'updated_at']
        
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value
    
    def validate_comment(self, value):
        if len(value) < 10:
            raise serializers.ValidationError(
                "Review comment must be at least 10 characters"
            )
        return value
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.user == request.user or request.user.is_staff
        return False
