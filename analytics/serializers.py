"""
Analytics Serializers
"""

from rest_framework import serializers
from .models import (
    DailyStats,
    AutomationPerformance,
    AIProviderMetrics,
    ContactEngagement,
    SystemEvent,
    WebhookLog
)


class DailyStatsSerializer(serializers.ModelSerializer):
    """Serializer for daily statistics"""
    
    class Meta:
        model = DailyStats
        fields = [
            'id', 'date', 'total_automations', 'active_automations',
            'total_triggers', 'successful_triggers', 'failed_triggers', 'skipped_triggers',
            'total_dms_sent', 'ai_enhanced_dms', 'avg_response_time',
            'success_rate', 'ai_enhancement_rate', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AutomationPerformanceSerializer(serializers.ModelSerializer):
    """Serializer for automation performance metrics"""
    automation_name = serializers.CharField(source='automation.name', read_only=True)
    
    class Meta:
        model = AutomationPerformance
        fields = [
            'id', 'automation', 'automation_name', 'date',
            'triggers_count', 'successful_count', 'failed_count', 'skipped_count',
            'avg_response_time', 'success_rate',
            'ai_enhanced_count', 'ai_enhancement_rate',
            'click_count', 'click_rate',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AIProviderMetricsSerializer(serializers.ModelSerializer):
    """Serializer for AI provider metrics"""
    
    class Meta:
        model = AIProviderMetrics
        fields = [
            'id', 'date', 'provider', 'model_used',
            'total_requests', 'successful_requests', 'failed_requests',
            'avg_response_time', 'total_tokens_used', 'estimated_cost',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ContactEngagementSerializer(serializers.ModelSerializer):
    """Serializer for contact engagement metrics"""
    contact_username = serializers.CharField(source='contact.instagram_username', read_only=True)
    
    class Meta:
        model = ContactEngagement
        fields = [
            'id', 'contact', 'contact_username', 'date',
            'dms_received', 'ai_enhanced_dms',
            'responses_count', 'avg_response_time',
            'button_clicks', 'link_clicks',
            'tags_added', 'tags_removed',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SystemEventSerializer(serializers.ModelSerializer):
    """Serializer for system events"""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = SystemEvent
        fields = [
            'id', 'user', 'username', 'event_type', 'description',
            'metadata', 'automation_id', 'instagram_account_id',
            'severity', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class WebhookLogSerializer(serializers.ModelSerializer):
    """Serializer for webhook logs"""
    instagram_username = serializers.CharField(
        source='instagram_account.username',
        read_only=True
    )
    
    class Meta:
        model = WebhookLog
        fields = [
            'id', 'instagram_account', 'instagram_username',
            'event_type', 'payload', 'processed', 'processed_at',
            'processing_error', 'response_status', 'response_data',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# Dashboard-specific serializers

class DashboardOverviewSerializer(serializers.Serializer):
    """Aggregated dashboard overview"""
    period = serializers.CharField()
    total_automations = serializers.IntegerField()
    active_automations = serializers.IntegerField()
    total_dms_sent = serializers.IntegerField()
    total_triggers = serializers.IntegerField()
    today_triggers = serializers.IntegerField()
    success_rate = serializers.FloatField()
    ai_enhancement_rate = serializers.FloatField()
    daily_breakdown = serializers.ListField()


class AutomationAnalyticsSerializer(serializers.Serializer):
    """Analytics for specific automation"""
    automation_id = serializers.UUIDField()
    automation_name = serializers.CharField()
    period_days = serializers.IntegerField()
    total_triggers = serializers.IntegerField()
    triggers_by_status = serializers.DictField()
    ai_enhanced_count = serializers.IntegerField()
    success_rate = serializers.FloatField()
    total_dms_sent = serializers.IntegerField()
    daily_breakdown = serializers.ListField()


class TopPerformersSerializer(serializers.Serializer):
    """Top performing automations"""
    id = serializers.UUIDField()
    name = serializers.CharField()
    total_triggers = serializers.IntegerField()
    success_rate = serializers.FloatField()
    total_dms_sent = serializers.IntegerField()


class AIUsageSerializer(serializers.Serializer):
    """AI usage statistics"""
    period = serializers.CharField()
    total_requests = serializers.IntegerField()
    successful_requests = serializers.IntegerField()
    failed_requests = serializers.IntegerField()
    models_breakdown = serializers.ListField()
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=4)
    avg_response_time = serializers.FloatField()


class RealtimeStatsSerializer(serializers.Serializer):
    """Real-time statistics for WebSocket"""
    timestamp = serializers.DateTimeField()
    active_automations = serializers.IntegerField()
    triggers_today = serializers.IntegerField()
    dms_sent_today = serializers.IntegerField()
    current_queue_size = serializers.IntegerField()
    ai_requests_today = serializers.IntegerField()