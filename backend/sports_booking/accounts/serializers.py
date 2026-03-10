from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import OTP

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    # Serializer for user details
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    total_bookings = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name','last_name',  'full_name', 'mobile_number', 'is_staff', 'is_mobile_verified', 'date_joined', 'total_bookings']
        read_only_fields = ['id', 'is_staff', 'date_joined']

    def get_total_bookings(self, obj):
        return obj.bookings.count() if hasattr(obj, 'bookings') else 0

class UserRegistrationSerializer(serializers.ModelSerializer):
    # Serializer for user registration
    password = serializers.CharField(
        write_only = True,
        required=False,
        validators=[validate_password]
    )
    confirm_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'mobile_number', 'password', 'confirm_password']
    
    def validate_mobile_number(self, value):
        # Validate mobile number format and uniqueness
        if len(value) != 10:
            raise serializers.ValidationError("Mobile number must be exactly 10 digits")
        if not value.isdigit():
            raise serializers.ValidationError("Mobile number must contain only digits")
        if User.objects.filter(mobile_number=value).exists():
            raise serializers.ValidationError("Mobile number already registered")
        return value
    
    def validate_username(self, value):
        # Validate username uniqueness
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        if len(value) < 3:
            raise serializers.ValidationError("Username must be atleast 3 characters")
        return value
    
    def validate_email(self, value):
        # Validate email uniqueness
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value
    
    def validate(self, data):
        # Validate password
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        if password and confirm_password:
            if password != confirm_password:
                raise serializers.ValidationError({
                    'confirm_password': "Password do not match"
                })
        return data
    
    def create(self, validated_data):
        # Create new user
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password', None)

        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        
        user.is_mobile_verified = True
        user.save()
        return user
    
class UserUpdateSerializer(serializers.ModelSerializer):
    # Serializer for updating user profile
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def validate_email(self,value):
        # Validate email uniqueness excluding current user
        user = self.instance
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("Email already in use")
        return value
    

class OTPSerializer(serializers.Serializer):
    # Serializer for sending OTP
    mobile_number = serializers.CharField(max_length=10, min_length=10)

    def validate_mobile_number(self, value):
        # Basic phone number validation
        if not value.isdigit():
            raise serializers.ValidationError("Mobile number must contain only digits")
        return value

class OTPVerifySerializer(serializers.Serializer):
    # Serializer for verifying OTP
    mobile_number = serializers.CharField(max_length=10, min_length=10)
    otp = serializers.CharField(max_length=6, min_length=6)

    def validate_mobile_number(self, value):
        # Validate mobile number format
        if not value.isdigit():
            raise serializers.ValidationError("Mobile number must contain only digits")
        return value

    def validate_otp(self, value):
        # Validate OTP
        if len(value) != 6 or not value.isdigit():
            raise serializers.ValidationError("OTP must be 6 digits")
        return value
    
class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True, 
        write_only=True,
        validators=[validate_password]
    )
    confirm_password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, data):
        """Validate password change"""
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': "Passwords do not match"
            })
        return data