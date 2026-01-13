"""
Instagram API Rate Limiting with Queue System
Handles 200 DMs/hour limit - EXACTLY like LinkPlease does it!

This is CRITICAL for production - without this, viral posts break your app!
"""

from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from celery import shared_task
from .models import AutomationTrigger, InstagramAccount
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# RATE LIMITER CLASS
# ============================================================================

class InstagramRateLimiter:
    """
    Manages Instagram API rate limits per account
    
    Limits:
    - 200 DMs per hour per account
    - 1 DM per user per 24 hours (from comment/story triggers)
    - 24-hour messaging window (can only message recent engagers)
    """
    
    DM_LIMIT_PER_HOUR = 200
    
    def __init__(self, instagram_account):
        self.instagram_account = instagram_account
        self.cache_key = f'dm_count:{instagram_account.id}:{self._get_hour_key()}'
        self.user_cache_prefix = f'dm_user:{instagram_account.id}'
    
    def _get_hour_key(self):
        """Get current hour key for rate limiting (e.g., '2026-01-10-14')"""
        now = timezone.now()
        return now.strftime('%Y-%m-%d-%H')
    
    def can_send_dm(self):
        """Check if we can send another DM this hour"""
        count = self._get_current_count()
        return count < self.DM_LIMIT_PER_HOUR
    
    def _get_current_count(self):
        """Get DM count for current hour"""
        count = cache.get(self.cache_key, 0)
        return int(count)
    
    def increment_count(self):
        """Increment DM count for current hour"""
        count = self._get_current_count()
        new_count = count + 1
        
        # Cache expires at end of hour
        minutes_left = 60 - timezone.now().minute
        cache.set(self.cache_key, new_count, timeout=minutes_left * 60)
        
        logger.info(f'📊 Rate limit: {new_count}/{self.DM_LIMIT_PER_HOUR} for @{self.instagram_account.username}')
        
        return new_count
    
    def get_remaining_quota(self):
        """Get remaining DMs for this hour"""
        return self.DM_LIMIT_PER_HOUR - self._get_current_count()
    
    def can_send_to_user(self, user_id):
        """Check if we can send DM to this specific user (24-hour rule)"""
        user_key = f'{self.user_cache_prefix}:{user_id}'
        last_sent = cache.get(user_key)
        
        if last_sent:
            # Already sent DM to this user in last 24 hours
            return False
        
        return True
    
    def mark_user_sent(self, user_id):
        """Mark that we sent DM to this user (24-hour cooldown)"""
        user_key = f'{self.user_cache_prefix}:{user_id}'
        cache.set(user_key, timezone.now().isoformat(), timeout=86400)  # 24 hours
    
    def get_reset_time(self):
        """Get time when rate limit resets (next hour)"""
        now = timezone.now()
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        return next_hour


# ============================================================================
# QUEUE MANAGER
# ============================================================================

class QueueManager:
    """
    Manages queued DM triggers
    
    When rate limit is hit:
    1. Trigger status set to 'queued'
    2. Queue processed every hour
    3. DMs sent when quota available
    """
    
    @staticmethod
    def queue_trigger(trigger):
        """Queue a trigger for later processing"""
        trigger.status = 'queued'
        trigger.queued_at = timezone.now()
        trigger.save()
        
        logger.info(f'⏳ Trigger #{trigger.id} queued - rate limit reached')
    
    @staticmethod
    def get_queued_triggers(instagram_account, limit=None):
        """Get queued triggers for an account (oldest first)"""
        queryset = AutomationTrigger.objects.filter(
            automation__instagram_account=instagram_account,
            status='queued'
        ).order_by('queued_at')  # FIFO - First In First Out
        
        if limit:
            queryset = queryset[:limit]
        
        return queryset
    
    @staticmethod
    def get_queue_size(instagram_account):
        """Get number of queued triggers"""
        return AutomationTrigger.objects.filter(
            automation__instagram_account=instagram_account,
            status='queued'
        ).count()
