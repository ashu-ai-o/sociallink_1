from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid

class User(AbstractUser):
    """Extended User model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    plan = models.CharField(
        max_length=20,
        choices=[('free', 'Free'), ('pro', 'Pro'), ('enterprise', 'Enterprise')],
        default='free'
    )
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
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


class InstagramAccount(models.Model):
    """Instagram account connection"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='instagram_accounts')
    instagram_user_id = models.CharField(max_length=100, unique=True)
    username = models.CharField(max_length=100)
    access_token = models.TextField()
    token_expires_at = models.DateTimeField()
    page_id = models.CharField(max_length=100)
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

