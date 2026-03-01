from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid

from core import settings

class User(AbstractUser):
    """Extended User model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)


    # Email verification
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    email_verification_sent_at = models.DateTimeField(blank=True, null=True)


    # Password reset
    password_reset_token = models.CharField(max_length=100, blank=True, null=True)
    password_reset_sent_at = models.DateTimeField(blank=True, null=True)

    # OAuth
    google_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    github_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    profile_picture = models.URLField(blank=True, null=True)

    # Additional fields
    phone = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    welcome_email_sent = models.BooleanField(
        default=False,
        help_text='Track if welcome email has been sent after email verification'
    )


    # Fix reverse accessor clash with auth.User
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',  # ← Instead of 'user_set'
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',  # ← Instead of 'user_set'
        related_query_name='custom_user',
    )

    # Cookie Consent Fields
    cookie_consent_given = models.BooleanField(
        default=False,
        help_text="Whether user has made a cookie choice"
    )
    cookie_consent_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When user gave/updated consent"
    )
    cookie_preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="Cookie consent preferences"
    )

    onboarding_completed = models.BooleanField(default=False, help_text="Whether user has completed onboarding flow")
    onboarding_step = models.PositiveSmallIntegerField(default=0, help_text="Current step in the onboarding flow (0 = not started)")

    email_preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="Email notification preferences"
    )

    # Default preferences:
    {
        'weekly_reports': True,
        'automation_alerts': True,
        'dm_failures': True,
        'account_issues': True
    }

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']


    # Two-Factor Authentication (2FA) fields
    two_factor_enabled = models.BooleanField(default=False, help_text="Enable/disable 2FA")
    two_factor_secret = models.CharField(max_length=32, blank=True, null=True, help_text="TOTP secret key")
    backup_codes = models.JSONField(default=list, blank=True, help_text="10 hashed backup codes for 2FA recovery")
    two_factor_enabled_at = models.DateTimeField(blank=True, null=True, help_text="When 2FA was enabled")

    # Email Preferences
    email_preferences = models.JSONField(
        default=dict,
        help_text="Email notification preferences",
        blank=True
    )


    # Notification Preferences
    notification_preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="In-app notification preferences"
    )
    
    # Timezone
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text="User's timezone for date/time display"
    )
    
    # Language
    language = models.CharField(
        max_length=10,
        default='en',
        help_text="Preferred language"
    )
    
    # Marketing
    marketing_opt_in = models.BooleanField(
        default=True,
        help_text="Opted in for marketing communications"
    )
    

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(blank=True, null=True)

    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email or self.username

    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login_at = timezone.now()
        self.save(update_fields=['last_login_at'])



    def get_email_preference(self, email_type: str) -> bool:
        """
        Get email preference for specific type
        Returns True if user wants to receive this email type
        """
        if not self.email_preferences:
            return True  # Default to sending all emails
        
        return self.email_preferences.get(email_type, True)
    
    def get_notification_preference(self, notification_type: str) -> bool:
        """
        Get notification preference for specific type
        Returns True if user wants to receive this notification type
        """
        if not self.notification_preferences:
            return True  # Default to allowing all notifications
        
        return self.notification_preferences.get(notification_type, True)

    def set_notification_preference(self, notification_type: str, enabled: bool):
        """Set notification preference for specific type"""
        if not self.notification_preferences:
            self.notification_preferences = {}
        
        self.notification_preferences[notification_type] = enabled
        self.save(update_fields=['notification_preferences', 'updated_at'])
    
    def set_email_preference(self, email_type: str, enabled: bool):
        """Set email preference for specific type"""
        if not self.email_preferences:
            self.email_preferences = {}
        
        self.email_preferences[email_type] = enabled
        self.save(update_fields=['email_preferences', 'updated_at'])
    
    def opt_out_all_emails(self):
        """Opt out of all non-critical emails"""
        self.email_preferences = {
            'payment_receipt': True,  # Critical, cannot opt out
            'payment_failure': True,  # Critical, cannot opt out
            'subscription_reminder': False,
            'marketing': False,
            'product_updates': False,
        }
        self.marketing_opt_in = False
        self.save()
    
    @classmethod
    def get_or_create_for_user(cls, user):
        """Get or create profile for user"""
        profile, created = cls.objects.get_or_create(
            user=user,
            defaults={
                'email_preferences': {
                    'payment_receipt': True,
                    'payment_failure': True,
                    'subscription_reminder': True,
                    'marketing': True,
                    'product_updates': True,
                    'account_notifications': True,
                    'security_alerts': True,
                    'token_usage_alerts': True,
                    'deployment_status': True,
                    'collaborator_invites': True,
                },
                'notification_preferences': {
                    'marketing_emails': True,
                    'account_notifications': True,
                    'security_alerts': True,
                    'product_updates': True,
                    'token_usage_alerts': True,
                    'deployment_status': True,
                    'collaborator_invites': True,
                    'billing_invoices': True,
                }
            }
        )
        return profile
    


class EmailVerificationToken(models.Model):
    """
    Email verification tokens with expiry
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_tokens')
    token = models.CharField(max_length=100, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        db_table = 'email_verification_tokens'
        ordering = ['-created_at']

    def is_valid(self):
        """Check if token is still valid"""
        return not self.is_used and timezone.now() < self.expires_at

    def mark_as_used(self):
        """Mark token as used"""
        self.is_used = True
        self.save(update_fields=['is_used'])




class CookieConsent(models.Model):
    """
    Detailed cookie consent history
    Tracks every time user updates their preferences
    For legal compliance and audit trail
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cookie_consents',
        null=True,
        blank=True  # Allow anonymous
    )
    
    # Consent Details
    essential = models.BooleanField(default=True)
    analytics = models.BooleanField(default=False)
    marketing = models.BooleanField(default=False)
    preferences = models.BooleanField(default=False)
    
    # Context
    consent_type = models.CharField(
        max_length=20,
        choices=[
            ('accept_all', 'Accept All'),
            ('reject_all', 'Reject All'),
            ('custom', 'Custom Selection'),
        ]
    )
    
    # Tracking
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    page_url = models.URLField(max_length=500, blank=True)
    
    # Metadata
    is_active = models.BooleanField(
        default=True,
        help_text="False when user updates preferences (superseded)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cookie_consents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_active']),
            models.Index(fields=['consent_type']),
        ]
    
    def __str__(self):
        user_str = self.user.email if self.user else 'Anonymous'
        return f"{user_str} - {self.consent_type} - {self.created_at}"






class PasswordResetToken(models.Model):
    """
    Password reset tokens with expiry
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=100, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        db_table = 'password_reset_tokens'
        ordering = ['-created_at']

    def is_valid(self):
        """Check if token is still valid"""
        return not self.is_used and timezone.now() < self.expires_at

    def mark_as_used(self):
        """Mark token as used"""
        self.is_used = True
        self.save(update_fields=['is_used'])








class PasswordChangeOTP(models.Model):
    """
    OTP tokens for password change requests
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='password_change_otps')
    otp_code = models.CharField(max_length=6, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)

    class Meta:
        db_table = 'password_change_otps'
        ordering = ['-created_at']

    def is_valid(self):
        """Check if OTP is still valid"""
        return not self.is_used and timezone.now() < self.expires_at and self.attempts < 3

    def mark_as_used(self):
        """Mark OTP as used"""
        self.is_used = True
        self.save(update_fields=['is_used'])

    def increment_attempts(self):
        """Increment failed attempts"""
        self.attempts += 1
        self.save(update_fields=['attempts'])


class ForgotPasswordOTP(models.Model):
    """
    OTP tokens for forgot password requests
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forgot_password_otps')
    otp_code = models.CharField(max_length=6, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)

    class Meta:
        db_table = 'forgot_password_otps'
        ordering = ['-created_at']

    def is_valid(self):
        """Check if OTP is still valid"""
        return not self.is_used and timezone.now() < self.expires_at and self.attempts < 3

    def mark_as_used(self):
        """Mark OTP as used"""
        self.is_used = True
        self.save(update_fields=['is_used'])






#session and user activity tracking models
class UserSession(models.Model):
    """
    Tracks user browsing sessions with comprehensive metadata
    Captures IP, location, device, browser, and platform information
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='browsing_sessions', null=True, blank=True)

    # Session identification
    session_key = models.CharField(max_length=255, blank=True)  # Django session key
    session_token = models.CharField(max_length=255, blank=True, unique=True)  # Custom tracking token
    refresh_jti = models.CharField(max_length=255, blank=True, null=True, help_text="JWT ID of the refresh token associated with this session")

    # IP and Network
    ip_address = models.GenericIPAddressField()
    ip_version = models.CharField(max_length=10, blank=True)  # 'IPv4' or 'IPv6'
    proxy_ip = models.GenericIPAddressField(null=True, blank=True)  # If behind proxy

    # Geolocation
    country = models.CharField(max_length=100, blank=True)
    country_code = models.CharField(max_length=10, blank=True)  # 'US', 'UK', etc.
    region = models.CharField(max_length=100, blank=True)  # State/Province
    city = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    timezone = models.CharField(max_length=100, blank=True)

    # ISP and Network Details
    isp = models.CharField(max_length=200, blank=True)  # Internet Service Provider
    organization = models.CharField(max_length=200, blank=True)
    asn = models.CharField(max_length=50, blank=True)  # Autonomous System Number

    # Browser Information
    browser_name = models.CharField(max_length=100, blank=True)  # Chrome, Firefox, Safari, etc.
    browser_version = models.CharField(max_length=50, blank=True)
    browser_language = models.CharField(max_length=20, blank=True)

    # Operating System
    os_name = models.CharField(max_length=100, blank=True)  # Windows, macOS, Linux, Android, iOS
    os_version = models.CharField(max_length=50, blank=True)

    # Device Information
    device_type = models.CharField(max_length=50, choices=[
        ('desktop', 'Desktop'),
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet'),
        ('bot', 'Bot/Crawler'),
        ('unknown', 'Unknown'),
    ], default='unknown')
    device_brand = models.CharField(max_length=100, blank=True)  # Apple, Samsung, etc.
    device_model = models.CharField(max_length=100, blank=True)  # iPhone 13, Galaxy S21, etc.
    is_mobile = models.BooleanField(default=False)
    is_tablet = models.BooleanField(default=False)
    is_touch_capable = models.BooleanField(default=False)
    is_pc = models.BooleanField(default=False)
    is_bot = models.BooleanField(default=False)

    # Screen and Display
    screen_resolution = models.CharField(max_length=50, blank=True)  # 1920x1080
    color_depth = models.IntegerField(null=True, blank=True)
    pixel_ratio = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # User Agent
    user_agent = models.TextField()  # Full user agent string
    user_agent_hash = models.CharField(max_length=64, blank=True)  # MD5/SHA hash for quick comparison

    # Referrer and Entry
    referrer_url = models.URLField(max_length=500, blank=True)
    referrer_domain = models.CharField(max_length=200, blank=True)
    landing_page = models.CharField(max_length=500, blank=True)
    utm_source = models.CharField(max_length=200, blank=True)
    utm_medium = models.CharField(max_length=200, blank=True)
    utm_campaign = models.CharField(max_length=200, blank=True)
    utm_term = models.CharField(max_length=200, blank=True)
    utm_content = models.CharField(max_length=200, blank=True)

    # Session Activity
    page_views = models.IntegerField(default=0)
    actions_count = models.IntegerField(default=0)
    duration_seconds = models.IntegerField(default=0)


    #add in admin fieldsets
    last_activity = models.DateTimeField(auto_now=True)

    # Security Flags
    is_vpn = models.BooleanField(default=False)
    is_proxy = models.BooleanField(default=False)
    is_tor = models.BooleanField(default=False)
    is_datacenter = models.BooleanField(default=False)
    threat_level = models.CharField(max_length=20, choices=[
        ('none', 'None'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], default='none')

    # Session Status
    is_active = models.BooleanField(default=True)
    login_method = models.CharField(max_length=50, blank=True)  # 'password', 'oauth_google', etc.
    session_ended_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Session {self.id} - {self.user} ({self.ip_address})"

    def get_location_string(self):
        """Return a human-readable location string"""
        parts = [p for p in [self.city, self.region, self.country] if p]
        return ', '.join(parts) if parts else 'Unknown location'

    def get_device_string(self):
        """Return a human-readable device string"""
        if self.device_brand and self.device_model:
            return f"{self.device_brand} {self.device_model}"
        if self.device_brand:
            return self.device_brand
        return self.get_device_type_display()

    def get_platform_string(self):
        """Return a human-readable platform string"""
        if self.os_name and self.os_version:
            return f"{self.os_name} {self.os_version}"
        return self.os_name or 'Unknown OS'

class PageVisit(models.Model):
    """
    Tracks individual page visits within a session
    Provides detailed analytics on user navigation
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    session = models.ForeignKey(UserSession, on_delete=models.CASCADE, related_name='page_visits')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='page_visits', null=True, blank=True)

    # Page Information
    url = models.CharField(max_length=500)
    path = models.CharField(max_length=500)
    query_string = models.TextField(blank=True)
    page_title = models.CharField(max_length=200, blank=True)

    # HTTP Details
    http_method = models.CharField(max_length=10, default='GET')
    http_status = models.IntegerField(null=True, blank=True)
    response_time_ms = models.IntegerField(null=True, blank=True)

    # Referrer
    referrer = models.URLField(max_length=500, blank=True)
    is_internal_referrer = models.BooleanField(default=True)

    # Timing
    time_on_page_seconds = models.IntegerField(default=0)
    scroll_depth_percentage = models.IntegerField(default=0)  # How far user scrolled

    # User Actions
    clicks = models.IntegerField(default=0)
    form_submissions = models.IntegerField(default=0)
    downloads = models.IntegerField(default=0)

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)

    # Timestamps
    visited_at = models.DateTimeField(auto_now_add=True)
    exited_at = models.DateTimeField(null=True, blank=True)






class UserEvent(models.Model):
    """
    Tracks specific user events and interactions
    For detailed behavioral analytics
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    session = models.ForeignKey(UserSession, on_delete=models.CASCADE, related_name='events', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='events', null=True, blank=True)

    # Event Details
    event_type = models.CharField(max_length=100, choices=[
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('signup', 'Sign Up'),
        ('project_create', 'Project Created'),
        ('project_update', 'Project Updated'),
        ('project_delete', 'Project Deleted'),
        ('deployment', 'Deployment'),
        ('error', 'Error Occurred'),
        ('button_click', 'Button Click'),
        ('form_submit', 'Form Submit'),
        ('share', 'Share'),
        ('search', 'Search'),
        ('filter', 'Filter'),
        ('sort', 'Sort'),
        ('custom', 'Custom Event'),
    ])
    event_name = models.CharField(max_length=200)
    event_category = models.CharField(max_length=100, blank=True)

    # Context
    page_url = models.CharField(max_length=500, blank=True)
    element_id = models.CharField(max_length=200, blank=True)  # DOM element ID
    element_class = models.CharField(max_length=200, blank=True)  # DOM element class
    element_text = models.CharField(max_length=500, blank=True)

    # Event Data
    event_value = models.CharField(max_length=500, blank=True)
    event_data = models.JSONField(default=dict, blank=True)

    # Success/Error
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)












class EnterpriseContact(models.Model):
    """
    Enterprise contact form submissions
    Stores inquiries from potential enterprise customers
    """
    
    # Status choices
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('converted', 'Converted'),
        ('closed', 'Closed'),
    ]
    
    # Company size choices
    COMPANY_SIZE_CHOICES = [
        ('1-10', '1-10 employees'),
        ('11-50', '11-50 employees'),
        ('51-200', '51-200 employees'),
        ('201-500', '201-500 employees'),
        ('501-1000', '501-1000 employees'),
        ('1000+', '1000+ employees'),
    ]
    
    # Primary fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Personal information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Company information
    company_name = models.CharField(max_length=200)
    company_size = models.CharField(max_length=20, choices=COMPANY_SIZE_CHOICES)
    job_title = models.CharField(max_length=100, blank=True, null=True)
    
    # Project details
    project_details = models.TextField(
        help_text='What are you looking to build?'
    )
    budget_range = models.CharField(max_length=50, blank=True, null=True)
    timeline = models.CharField(max_length=50, blank=True, null=True)
    
    # Lead management
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        db_index=True
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_contacts',
        help_text='Sales rep assigned to this lead'
    )
    
    # Metadata
    source = models.CharField(
        max_length=50,
        default='website',
        help_text='Where did this lead come from?'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # Notes
    internal_notes = models.TextField(
        blank=True,
        null=True,
        help_text='Internal notes (not visible to customer)'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    contacted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'enterprise_contacts'
        ordering = ['-created_at']
        verbose_name = 'Enterprise Contact'
        verbose_name_plural = 'Enterprise Contacts'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.company_name}"
    
    def get_full_name(self):
        """Return full name"""
        return f"{self.first_name} {self.last_name}"
    
    def mark_as_contacted(self):
        """Mark lead as contacted"""
        self.status = 'contacted'
        self.contacted_at = timezone.now()
        self.save(update_fields=['status', 'contacted_at', 'updated_at'])


class Feedback(models.Model):
    """User feedback, bug reports, and feature requests."""

    CATEGORY_CHOICES = [
        ('bug', 'Bug Report'),
        ('feature', 'Feature Request'),
        ('general', 'General Feedback'),
        ('ux', 'UX / Design'),
        ('performance', 'Performance'),
        ('other', 'Other'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_review', 'In Review'),
        ('planned', 'Planned'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='feedback_submissions',
    )
    # Anonymous submitters
    email = models.EmailField(blank=True, default='')
    name = models.CharField(max_length=120, blank=True, default='')

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    # Optional: attach a project
    project_id = models.UUIDField(null=True, blank=True)

    # Rating (1–5 stars, optional)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)

    # Admin notes
    admin_notes = models.TextField(blank=True, default='')

    # Meta
    page_url = models.CharField(max_length=500, blank=True, default='')
    user_agent = models.CharField(max_length=500, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_feedback'
        ordering = ['-created_at']
        verbose_name = 'Feedback'
        verbose_name_plural = 'Feedback'

    def __str__(self):
        submitter = self.user.email if self.user else (self.email or 'Anonymous')
        return f"[{self.get_category_display()}] {self.title} – {submitter}"
























class InstagramAccount(models.Model):
    """Instagram account connection"""
    CONNECTION_CHOICES = [
        ('facebook_graph', 'Facebook Graph API (Legacy)'),
        ('instagram_platform', 'Instagram Platform API (Direct)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='instagram_accounts')
    instagram_user_id = models.CharField(max_length=100, unique=True, help_text="Graph API user ID")
    platform_id = models.CharField(max_length=100, blank=True, null=True, help_text="New Instagram Platform user ID")
    username = models.CharField(max_length=100)
    access_token = models.TextField()
    token_expires_at = models.DateTimeField()
    
    connection_method = models.CharField(
        max_length=50, 
        choices=CONNECTION_CHOICES, 
        default='facebook_graph'
    )
    
    # page_id is only needed for facebook_graph connection
    page_id = models.CharField(max_length=100, blank=True, null=True)
    
    profile_picture_url = models.URLField(blank=True)
    followers_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    last_synced = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'instagram_accounts'
        ordering = ['-created_at']

    def __str__(self):
        return f"@{self.username}"

