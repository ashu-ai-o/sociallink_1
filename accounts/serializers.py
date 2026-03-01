"""
User and Authentication Serializers
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import User, InstagramAccount
import re

User = get_user_model()


class EmailPreferencesSerializer(serializers.Serializer):
    payment_receipt = serializers.BooleanField(default=True, read_only=True)
    payment_failure = serializers.BooleanField(default=True, read_only=True)
    subscription_reminder = serializers.BooleanField(default=True)
    marketing = serializers.BooleanField(default=False)
    product_updates = serializers.BooleanField(default=True)
    
    def validate_payment_receipt(self, value):
        # Critical emails cannot be disabled
        return True
    
    def validate_payment_failure(self, value):
        # Critical emails cannot be disabled
        return True


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'bio', 'profile_picture', 'is_email_verified',
            'onboarding_completed', 'onboarding_step',
            'email_preferences', 'notification_preferences',
            'created_at', 'last_login_at'
        )
        read_only_fields = ('id', 'is_email_verified', 'created_at', 'last_login_at')

    def update(self, instance, validated_data):
        # Handle profile picture upload
        profile_picture = validated_data.get('profile_picture')
        if profile_picture:
            # Delete old profile picture if it exists
            if instance.profile_picture and instance.profile_picture.startswith('/media/'):
                old_file_path = instance.profile_picture.replace('/media/', '')
                if default_storage.exists(old_file_path):
                    default_storage.delete(old_file_path)

            # Save new profile picture
            file_name = f"profile_pictures/{instance.id}_{profile_picture.name}"
            file_path = default_storage.save(file_name, ContentFile(profile_picture.read()))
            validated_data['profile_picture'] = f"/media/{file_path}"

        return super().update(instance, validated_data)


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        # ✅ RESTRICT TO GMAIL AND YAHOO ONLY
        email = attrs.get('email', '').lower()
        allowed_domains_pattern = r'^[a-zA-Z0-9._%+-]+@(gmail\.com|yahoo\.com)$'

        if not re.match(allowed_domains_pattern, email):
            raise serializers.ValidationError({
                "email": "Only Gmail (@gmail.com) and Yahoo (@yahoo.com) email addresses are allowed for registration."
            })

        # Check if email already exists
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Email is already registered."})

        # Check if username already exists
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({"username": "Username is already taken."})

        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            # Get user by email
            try:
                user_obj = User.objects.get(email=email)
            except User.DoesNotExist:
                print(f"[LOGIN DEBUG] No user found with email: {email}")
                raise serializers.ValidationError("Invalid credentials.")

            # Authenticate using email (USERNAME_FIELD = 'email')
            # Debug: check if password is correct before authenticate
            pwd_check = user_obj.check_password(password)
            print(f"[LOGIN DEBUG] check_password result for {email}: {pwd_check}")
            print(f"[LOGIN DEBUG] user_obj.is_active={user_obj.is_active}, username={user_obj.username}")

            user = authenticate(email=email, password=password)

            if not user:
                print(f"[LOGIN DEBUG] authenticate() failed for email={email} (check_password={pwd_check})")
                raise serializers.ValidationError("Invalid credentials.")

            if not user.is_active:
                print(f"[LOGIN DEBUG] User {email} is inactive")
                raise serializers.ValidationError("User account is disabled.")

            print(f"[LOGIN DEBUG] Login successful for {email}")
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError("Must include 'email' and 'password'.")


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password2 = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer for email verification"""
    token = serializers.CharField(required=True)


class GoogleAuthSerializer(serializers.Serializer):
    """Serializer for Google OAuth"""
    google_token = serializers.CharField(required=True, write_only=True)







class TwoFactorSetupSerializer(serializers.Serializer):
    """No input needed - just POST to initiate setup"""
    pass


class TwoFactorVerifySetupSerializer(serializers.Serializer):
    """Verify 2FA setup"""
    token = serializers.CharField(
        required=True,
        min_length=6,
        max_length=6,
        help_text="6-digit code from authenticator app"
    )
    secret = serializers.CharField(
        required=True,
        help_text="Secret key from setup step"
    )

    def validate_token(self, value):
        """Ensure token is 6 digits"""
        if not value.isdigit():
            raise serializers.ValidationError("Token must be 6 digits")
        return value

    def validate_secret(self, value):
        """Ensure secret is valid base32"""
        import base64
        try:
            # Check if it's valid base32
            base64.b32decode(value.upper())
            return value
        except Exception:
            raise serializers.ValidationError("Invalid secret key format")


class TwoFactorVerifyLoginSerializer(serializers.Serializer):
    """Verify 2FA during login"""
    email = serializers.EmailField(required=False)
    password = serializers.CharField(required=False, write_only=True)
    token = serializers.CharField(
        required=True,
        help_text="6-digit code from authenticator app or 8-character backup code"
    )
    
    def validate(self, attrs):
        # Either (email + password) OR authenticated via middleware
        has_credentials = 'email' in attrs and 'password' in attrs
        if not has_credentials:
            # Will be validated by middleware/view
            pass
        return attrs


class TwoFactorDisableSerializer(serializers.Serializer):
    """Disable 2FA"""
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text="Current account password"
    )
    token = serializers.CharField(
        required=True,
        help_text="6-digit code from authenticator app"
    )

    def validate_password(self, value):
        """Verify password is correct"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Incorrect password")
        return value


class TwoFactorRegenerateBackupCodesSerializer(serializers.Serializer):
    """Regenerate backup codes - only requires token verification"""
    token = serializers.CharField(
        required=True,
        help_text="6-digit code from authenticator app"
    )










from .models import EnterpriseContact

class EnterpriseContactSerializer(serializers.ModelSerializer):
    """
    Serializer for enterprise contact form
    Validates and saves contact submissions
    """
    
    class Meta:
        model = EnterpriseContact
        fields = (
            'first_name',
            'last_name',
            'email',
            'phone',
            'company_name',
            'company_size',
            'job_title',
            'project_details',
            'budget_range',
            'timeline',
        )
        extra_kwargs = {
            'phone': {'required': False},
            'job_title': {'required': False},
            'budget_range': {'required': False},
            'timeline': {'required': False},
        }
    
    def validate_email(self, value):
        """Validate email format"""
        if not value or '@' not in value:
            raise serializers.ValidationError("Please provide a valid email address.")
        return value.lower()
    
    def validate_first_name(self, value):
        """Validate first name"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("First name must be at least 2 characters.")
        return value.strip()
    
    def validate_last_name(self, value):
        """Validate last name"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Last name must be at least 2 characters.")
        return value.strip()
    
    def validate_company_name(self, value):
        """Validate company name"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Company name must be at least 2 characters.")
        return value.strip()
    
    def validate_project_details(self, value):
        """Validate project details"""
        if not value or len(value.strip()) < 20:
            raise serializers.ValidationError(
                "Please provide more details about your project (at least 20 characters)."
            )
        return value.strip()


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        from .models import Feedback
        model = Feedback
        fields = [
            'id', 'category', 'title', 'message', 'rating',
            'email', 'name', 'page_url', 'priority',
            # read-only
            'status', 'created_at',
        ]
        read_only_fields = ['id', 'status', 'created_at']

    def validate_title(self, value):
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters.")
        return value.strip()

    def validate_message(self, value):
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError("Message must be at least 10 characters.")
        return value.strip()

    def validate_rating(self, value):
        if value is not None and not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value






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
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'phone', 'bio', 'profile_picture', 'is_email_verified',
            'onboarding_completed', 'onboarding_step',
            'email_preferences', 'notification_preferences',
            'instagram_accounts', 'created_at', 'updated_at', 'last_login_at'
        ]
        read_only_fields = ['id', 'email', 'is_email_verified', 'created_at', 'updated_at', 'last_login_at']

    def update(self, instance, validated_data):
        # Handle profile picture upload
        profile_picture = validated_data.get('profile_picture')
        if profile_picture:
            from django.core.files.storage import default_storage
            from django.core.files.base import ContentFile
            # Delete old profile picture if it exists
            if instance.profile_picture and instance.profile_picture.startswith('/media/'):
                old_file_path = instance.profile_picture.replace('/media/', '')
                if default_storage.exists(old_file_path):
                    default_storage.delete(old_file_path)

            # Save new profile picture
            file_name = f"profile_pictures/{instance.id}_{profile_picture.name}"
            file_path = default_storage.save(file_name, ContentFile(profile_picture.read()))
            validated_data['profile_picture'] = f"/media/{file_path}"

        return super().update(instance, validated_data)