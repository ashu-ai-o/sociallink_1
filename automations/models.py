"""
Automation Models - WITH COMMENT REPLY FEATURE
"""

from django.db import models
import uuid
from accounts.models import InstagramAccount


class Automation(models.Model):
    """Core automation model with comment reply support"""
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
    trigger_keywords = models.JSONField(default=list, blank=True)
    trigger_match_type = models.CharField(
        max_length=20,
        choices=[
            ('exact', 'Exact Match'), 
            ('contains', 'Contains'), 
            ('any', 'Any Comment')
        ],
        default='exact'
    )
    
    # Target content
    target_posts = models.JSONField(default=list, blank=True)
    
    # ═══════════════════════════════════════════════════════════════
    # NEW FEATURE: Comment Reply (Public Response)
    # ═══════════════════════════════════════════════════════════════
    
    enable_comment_reply = models.BooleanField(
        default=True,
        help_text="Reply to the comment publicly before sending DM"
    )
    
    comment_reply_message = models.CharField(
        max_length=200,
        blank=True,
        default="✅ Sent! Check your DM",
        help_text="Public reply to the comment. Use {username} for personalization."
    )
    
    # ═══════════════════════════════════════════════════════════════
    
    # DM Response settings (Private)
    dm_message = models.TextField(
        help_text="Private message sent via DM (can include links)"
    )
    dm_buttons = models.JSONField(default=list, blank=True)
    
    # Follow settings
    require_follow = models.BooleanField(
        default=False,
        help_text="If True, user must follow before receiving DM"
    )
    follow_check_message = models.TextField(
        blank=True, 
        default=""
    )
    
    # AI Enhancement
    use_ai_enhancement = models.BooleanField(default=False)
    ai_context = models.TextField(blank=True)
    
    # Limits and controls
    max_triggers_per_user = models.IntegerField(default=1)
    cooldown_minutes = models.IntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)
    
    # Stats
    total_triggers = models.IntegerField(default=0)
    total_dms_sent = models.IntegerField(default=0)
    total_comment_replies = models.IntegerField(
        default=0,
        help_text="Number of public comment replies sent"
    )  # NEW!
    
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
    
    @property
    def success_rate(self):
        """Calculate DM success rate"""
        if self.total_triggers == 0:
            return 0
        return (self.total_dms_sent / self.total_triggers) * 100
    
    @property
    def comment_reply_rate(self):
        """Calculate comment reply success rate"""
        if self.total_triggers == 0:
            return 0
        return (self.total_comment_replies / self.total_triggers) * 100


class AutomationTrigger(models.Model):
    """Log of automation triggers with comment reply tracking"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    automation = models.ForeignKey(
        Automation, 
        on_delete=models.CASCADE, 
        related_name='triggers'
    )
    
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
    
    # ═══════════════════════════════════════════════════════════════
    # NEW: Comment Reply Tracking
    # ═══════════════════════════════════════════════════════════════
    
    comment_reply_sent = models.BooleanField(
        default=False,
        help_text="Whether public comment reply was sent"
    )  # NEW!
    
    comment_reply_text = models.CharField(
        max_length=200,
        blank=True,
        help_text="The actual reply text sent to the comment"
    )  # NEW!
    
    comment_reply_sent_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When the comment reply was sent"
    )  # NEW!
    
    # ═══════════════════════════════════════════════════════════════
    
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
            models.Index(fields=['comment_id']),  # NEW!
        ]

    def __str__(self):
        return f"{self.automation.name} - @{self.instagram_username}"


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

    def __str__(self):
        return f"@{self.instagram_username}"


class AutomationVariant(models.Model):
    """A/B testing variants"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    automation = models.ForeignKey(
        Automation, 
        on_delete=models.CASCADE, 
        related_name='variants'
    )
    name = models.CharField(max_length=200)
    
    # Variant settings
    dm_message = models.TextField()
    dm_buttons = models.JSONField(default=list, blank=True)
    comment_reply_message = models.CharField(
        max_length=200, 
        blank=True
    )  # NEW!
    
    # A/B test configuration
    traffic_percentage = models.IntegerField(default=50)
    is_active = models.BooleanField(default=True)
    
    # Performance metrics
    total_sends = models.IntegerField(default=0)
    total_clicks = models.IntegerField(default=0)
    total_conversions = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def conversion_rate(self):
        if self.total_sends == 0:
            return 0
        return (self.total_conversions / self.total_sends * 100)
    
    @property
    def click_rate(self):
        if self.total_sends == 0:
            return 0
        return (self.total_clicks / self.total_sends * 100)

    class Meta:
        db_table = 'automation_variants'

    def __str__(self):
        return f"{self.automation.name} - {self.name}"


# ═══════════════════════════════════════════════════════════════
# MIGRATION NOTES:
# ═══════════════════════════════════════════════════════════════
#
# Run these commands after updating models.py:
#
# python manage.py makemigrations automations
# python manage.py migrate
#
# New fields added to Automation:
# - enable_comment_reply (BooleanField, default=True)
# - comment_reply_message (CharField, default="✅ Sent! Check your DM")
# - total_comment_replies (IntegerField, default=0)
#
# New fields added to AutomationTrigger:
# - comment_reply_sent (BooleanField, default=False)
# - comment_reply_text (CharField, blank=True)
# - comment_reply_sent_at (DateTimeField, null=True)
#
# ═══════════════════════════════════════════════════════════════