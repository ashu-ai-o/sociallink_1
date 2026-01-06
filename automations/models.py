from django.db import models

# Create your models here.
from celery import uuid
from django.db import models
import uuid
from accounts.models import InstagramAccount

# Create your models here.
class Automation(models.Model):
    """Core automation model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instagram_account = models.ForeignKey(
        InstagramAccount, 
        on_delete=models.CASCADE, 
        related_name='automations'
    )
    name = models.CharField(max_length=200)
    
    # Trigger settings
    trigger_type = models.CharField(
        max_length=50,
        choices=[
            ('comment', 'Comment on Post'),
            ('story_mention', 'Story Mention'),
            ('story_reply', 'Story Reply'),
            ('dm_keyword', 'DM Keyword'),
        ]
    )
    trigger_keywords = models.JSONField(default=list, blank=True)  # ['keyword1', 'keyword2']
    trigger_match_type = models.CharField(
        max_length=20,
        choices=[('exact', 'Exact Match'), ('contains', 'Contains'), ('any', 'Any Comment')],
        default='exact'
    )
    
    # Target content
    target_posts = models.JSONField(default=list, blank=True)  # List of post IDs or 'all'
    
    # Response settings
    dm_message = models.TextField()
    dm_buttons = models.JSONField(default=list, blank=True)  # [{'text': 'Get Link', 'url': 'https://...'}]
    
    # Advanced features
    require_follow = models.BooleanField(default=False)
    follow_check_message = models.TextField(blank=True, default="Please follow us first to receive the link!")
    
    # AI Enhancement
    use_ai_enhancement = models.BooleanField(default=False)
    ai_context = models.TextField(blank=True, help_text="Context for AI to personalize responses")
    
    # Limits and controls
    max_triggers_per_user = models.IntegerField(default=1, help_text="How many times a user can trigger this")
    cooldown_minutes = models.IntegerField(default=0, help_text="Minutes to wait before re-triggering")
    
    # Status
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0, help_text="Higher priority automations run first")
    
    # Stats
    total_triggers = models.IntegerField(default=0)
    total_dms_sent = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'automations'
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['instagram_account', 'is_active']),
            models.Index(fields=['trigger_type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.trigger_type})"


class AutomationTrigger(models.Model):
    """Log of automation triggers"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    automation = models.ForeignKey(Automation, on_delete=models.CASCADE, related_name='triggers')
    
    # Instagram data
    instagram_user_id = models.CharField(max_length=100)
    instagram_username = models.CharField(max_length=100, blank=True)
    post_id = models.CharField(max_length=100, blank=True)
    comment_id = models.CharField(max_length=100, blank=True)
    comment_text = models.TextField(blank=True)
    
    # Processing
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('sent', 'DM Sent'),
            ('failed', 'Failed'),
            ('skipped', 'Skipped'),
        ],
        default='pending'
    )
    failure_reason = models.TextField(blank=True)
    
    # DM details
    dm_sent_at = models.DateTimeField(null=True, blank=True)
    dm_message_sent = models.TextField(blank=True)
    
    # AI enhancement
    was_ai_enhanced = models.BooleanField(default=False)
    ai_modifications = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'automation_triggers'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['automation', 'instagram_user_id']),
            models.Index(fields=['status', 'created_at']),
        ]


class Contact(models.Model):
    """Lead/Contact database"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instagram_account = models.ForeignKey(
        InstagramAccount,
        on_delete=models.CASCADE,
        related_name='contacts'
    )
    instagram_user_id = models.CharField(max_length=100)
    instagram_username = models.CharField(max_length=100)
    full_name = models.CharField(max_length=200, blank=True)
    profile_picture_url = models.URLField(blank=True)
    
    # Engagement stats
    total_interactions = models.IntegerField(default=0)
    total_dms_received = models.IntegerField(default=0)
    first_interaction = models.DateTimeField(auto_now_add=True)
    last_interaction = models.DateTimeField(auto_now=True)
    
    # Segmentation
    tags = models.JSONField(default=list, blank=True)
    custom_fields = models.JSONField(default=dict, blank=True)
    
    # Status
    is_follower = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)

    class Meta:
        db_table = 'contacts'
        unique_together = ['instagram_account', 'instagram_user_id']
        indexes = [
            models.Index(fields=['instagram_account', 'last_interaction']),
        ]




class AutomationVariant(models.Model):
    """A/B testing variants for automations"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    automation = models.ForeignKey(Automation, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=200)
    
    # Variant-specific settings
    dm_message = models.TextField()
    dm_buttons = models.JSONField(default=list, blank=True)
    
    # A/B test configuration
    traffic_percentage = models.IntegerField(default=50, help_text="0-100%")
    is_active = models.BooleanField(default=True)
    
    # Performance metrics
    total_sends = models.IntegerField(default=0)
    total_clicks = models.IntegerField(default=0)
    total_conversions = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def conversion_rate(self):
        return (self.total_conversions / self.total_sends * 100) if self.total_sends > 0 else 0
    
    @property
    def click_rate(self):
        return (self.total_clicks / self.total_sends * 100) if self.total_sends > 0 else 0
