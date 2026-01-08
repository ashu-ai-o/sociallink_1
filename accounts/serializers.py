"""
User and Authentication Serializers
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, InstagramAccount

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'plan', 'subscription_end_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password_confirm', 'first_name', 'last_name']
    
    def validate(self, attrs):
        """Validate passwords match"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        return attrs
    
    def create(self, validated_data):
        """Create new user"""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Authenticate user"""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,  # Django uses 'username' but we pass email
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    'Unable to log in with provided credentials.'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    'User account is disabled.'
                )
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                'Must include "email" and "password".'
            )


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change"""
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate_old_password(self, value):
        """Validate old password"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value
    
    def validate(self, attrs):
        """Validate new passwords match"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password": "New password fields didn't match."
            })
        return attrs
    
    def save(self):
        """Update password"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class InstagramAccountSerializer(serializers.ModelSerializer):
    """Serializer for Instagram Account"""
    
    class Meta:
        model = InstagramAccount
        fields = [
            'id', 'username', 'instagram_user_id', 'profile_picture_url',
            'followers_count', 'is_active', 'last_synced', 'created_at'
        ]
        read_only_fields = ['id', 'last_synced', 'created_at']


class InstagramAccountConnectSerializer(serializers.Serializer):
    """Serializer for connecting Instagram account"""
    access_token = serializers.CharField(required=True)
    instagram_user_id = serializers.CharField(required=True)
    username = serializers.CharField(required=True)
    page_id = serializers.CharField(required=True)
    token_expires_at = serializers.DateTimeField(required=True)
    profile_picture_url = serializers.URLField(required=False, allow_blank=True)
    followers_count = serializers.IntegerField(required=False, default=0)
    
    def create(self, validated_data):
        """Create Instagram account connection"""
        user = self.context['request'].user
        
        # Check if account already exists
        instagram_account, created = InstagramAccount.objects.update_or_create(
            instagram_user_id=validated_data['instagram_user_id'],
            defaults={
                'user': user,
                'username': validated_data['username'],
                'access_token': validated_data['access_token'],
                'token_expires_at': validated_data['token_expires_at'],
                'page_id': validated_data['page_id'],
                'profile_picture_url': validated_data.get('profile_picture_url', ''),
                'followers_count': validated_data.get('followers_count', 0),
                'is_active': True,
            }
        )
        
        return instagram_account


class UserProfileSerializer(serializers.ModelSerializer):
    """Detailed user profile with Instagram accounts"""
    instagram_accounts = InstagramAccountSerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'plan', 'subscription_end_date', 'instagram_accounts',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'email', 'created_at', 'updated_at']