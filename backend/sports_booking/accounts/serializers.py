from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import OTP

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone_number', 'first_name', 'last_name', 'is_phone_verified', 'date_joined']
        read_only_fields = ['id', 'is_phone_verified', 'date_joined']

class SendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)

    def validate_phone_number(self, value):
        # Basic phone number validation
        if not value.startswith('+'):
            value = '+91' + value.lstrip('0')

        # Remove spaces and special characters
        cleaned = ''.join(filter(str.isdigit, value.replace('+', '')))

        if len(cleaned) < 10:
            raise serializers.ValidationError("Please enter a valid phone number")
        
        return '+91' + cleaned[-10:]    # Always return Indian format

class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)

    def validate_otp(self, value):
        if len(value) != 6 or not value.isdigit():
            raise serializers.ValidationError("OTP must be 6 digits")
        return value
    