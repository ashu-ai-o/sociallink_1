"""
Analytics Models for tracking system performance
"""

from django.db import models
from django.utils import timezone
import uuid


class DailyStats(models.Model):
    """Daily aggregated statistics per user"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='daily_stats')
    date = models.DateField()
    
    # Automation stats
    total_automations = models.IntegerField(default=0)
    active_automations = models.IntegerField(default=0)
    
    # Trigger stats
    total_triggers = models.IntegerField(default=0)
    successful_triggers = models.IntegerField(default=0)
    failed_triggers = models.IntegerField(default=0)
    skipped_triggers = models.IntegerField(default=0)
    
    # DM stats
    total_dms_sent = models.IntegerField(default=0)
    ai_enhanced_dms = models.IntegerField(default=0)
    
    # Performance stats
    avg_response_time = models.FloatField(default=0.0, help_text="Average time to send DM (seconds)")
    success_rate = models.FloatField(default=0.0, help_text="Percentage of successful DMs")
    ai_enhancement_rate = models.FloatField(default=0.0, help_text="Percentage of AI-enhanced messages")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'daily_stats'
        unique_together = ['user', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user', '-date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.date}"


class AutomationPerformance(models.Model):
    """Performance metrics per automation"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    automation = models.ForeignKey(
        'automations.Automation',
        on_delete=models.CASCADE,
        related_name='performance_metrics'
    )
    date = models.DateField()
    
    # Trigger metrics
    triggers_count = models.IntegerField(default=0)
    successful_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)
    skipped_count = models.IntegerField(default=0)
    
    # Performance
    avg_response_time = models.FloatField(default=0.0)
    success_rate = models.FloatField(default=0.0)
    
    # AI metrics
    ai_enhanced_count = models.IntegerField(default=0)
    ai_enhancement_rate = models.FloatField(default=0.0)
    
    # Engagement (if available)
    click_count = models.IntegerField(default=0, help_text="Clicks on DM buttons")
    click_rate = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'automation_performance'
        unique_together = ['automation', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['automation', '-date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.automation.name} - {self.date}"


class AIProviderMetrics(models.Model):
    """Track AI provider usage and performance"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='ai_metrics')
    date = models.DateField()
    
    # Provider/Model info
    provider = models.CharField(max_length=50, default='openrouter')
    model_used = models.CharField(max_length=100)
    
    # Usage metrics
    total_requests = models.IntegerField(default=0)
    successful_requests = models.IntegerField(default=0)
    failed_requests = models.IntegerField(default=0)
    
    # Performance metrics
    avg_response_time = models.FloatField(default=0.0, help_text="Average AI response time (seconds)")
    total_tokens_used = models.IntegerField(default=0)
    
    # Cost tracking
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=4, default=0.0, help_text="Estimated cost in USD")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_provider_metrics'
        unique_together = ['user', 'date', 'model_used']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user', '-date']),
            models.Index(fields=['model_used']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.model_used} - {self.date}"


class ContactEngagement(models.Model):
    """Track engagement metrics per contact"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contact = models.ForeignKey(
        'automations.Contact',
        on_delete=models.CASCADE,
        related_name='engagement_metrics'
    )
    date = models.DateField()
    
    # Interaction metrics
    dms_received = models.IntegerField(default=0)
    ai_enhanced_dms = models.IntegerField(default=0)
    
    # Response metrics (if trackable)
    responses_count = models.IntegerField(default=0)
    avg_response_time = models.FloatField(default=0.0, help_text="Hours to respond")
    
    # Engagement
    button_clicks = models.IntegerField(default=0)
    link_clicks = models.IntegerField(default=0)
    
    # Tags/Segmentation changes
    tags_added = models.JSONField(default=list, blank=True)
    tags_removed = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'contact_engagement'
        unique_together = ['contact', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['contact', '-date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.contact.instagram_username} - {self.date}"


class SystemEvent(models.Model):
    """Log important system events for analytics"""
    
    EVENT_TYPES = [
        ('automation_created', 'Automation Created'),
        ('automation_activated', 'Automation Activated'),
        ('automation_deactivated', 'Automation Deactivated'),
        ('automation_deleted', 'Automation Deleted'),
        ('instagram_connected', 'Instagram Account Connected'),
        ('instagram_disconnected', 'Instagram Account Disconnected'),
        ('rate_limit_hit', 'Rate Limit Hit'),
        ('ai_provider_error', 'AI Provider Error'),
        ('dm_send_error', 'DM Send Error'),
        ('user_upgraded', 'User Plan Upgraded'),
        ('user_downgraded', 'User Plan Downgraded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='system_events',
        null=True,
        blank=True
    )
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    
    # Event details
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Related objects (optional)
    automation_id = models.UUIDField(null=True, blank=True)
    instagram_account_id = models.UUIDField(null=True, blank=True)
    
    # Severity
    severity = models.CharField(
        max_length=20,
        choices=[
            ('info', 'Info'),
            ('warning', 'Warning'),
            ('error', 'Error'),
            ('critical', 'Critical'),
        ],
        default='info'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'system_events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['event_type', '-created_at']),
            models.Index(fields=['severity', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.created_at}"


class WebhookLog(models.Model):
    """Log webhook events from Instagram"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instagram_account = models.ForeignKey(
        'accounts.InstagramAccount',
        on_delete=models.CASCADE,
        related_name='webhook_logs',
        null=True,
        blank=True
    )
    
    # Webhook data
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    
    # Processing
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    processing_error = models.TextField(blank=True)
    
    # Response
    response_status = models.IntegerField(null=True, blank=True)
    response_data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'webhook_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['instagram_account', '-created_at']),
            models.Index(fields=['event_type', '-created_at']),
            models.Index(fields=['processed', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.created_at}"