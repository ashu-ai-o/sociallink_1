# ============================================================================
# COMPLETE tasks.py - WITH RATE LIMITING + COMMENT REPLIES
# ============================================================================

"""
Celery Tasks - Production Ready
- Rate limiting (200 DMs/hour per account)
- Queue system for viral posts
- Comment reply feature
- AI enhancement
- WebSocket notifications
"""

import asyncio
from celery import shared_task
from channels.layers import get_channel_layer
from django.core.cache import cache
from django.utils import timezone
from django.db.models import F
import logging



logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


# ============================================================================
# RATE LIMITING CLASSES
# ============================================================================

class InstagramRateLimiter:
    """
    Manages Instagram API rate limits per account
    
    Limits:
    - 200 DMs per hour per account
    - 1 DM per user per 24 hours
    """
    
    DM_LIMIT_PER_HOUR = 200
    
    def __init__(self, instagram_account):
        self.instagram_account = instagram_account
        self.cache_key = f'dm_count:{instagram_account.id}:{self._get_hour_key()}'
        self.user_cache_prefix = f'dm_user:{instagram_account.id}'
    
    def _get_hour_key(self):
        """Get current hour key (e.g., '2026-01-10-14')"""
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
        """Check if we can send DM to this user (24-hour rule)"""
        user_key = f'{self.user_cache_prefix}:{user_id}'
        last_sent = cache.get(user_key)
        
        if last_sent:
            return False
        
        return True
    
    def mark_user_sent(self, user_id):
        """Mark that we sent DM to this user (24-hour cooldown)"""
        user_key = f'{self.user_cache_prefix}:{user_id}'
        cache.set(user_key, timezone.now().isoformat(), timeout=86400)
    
    def get_reset_time(self):
        """Get time when rate limit resets (next hour)"""
        from datetime import timedelta
        now = timezone.now()
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        return next_hour


class QueueManager:
    """Manages queued DM triggers"""
    
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
        from .models import AutomationTrigger
        
        queryset = AutomationTrigger.objects.filter(
            automation__instagram_account=instagram_account,
            status='queued'
        ).order_by('queued_at')
        
        if limit:
            queryset = queryset[:limit]
        
        return queryset
    
    @staticmethod
    def get_queue_size(instagram_account):
        """Get number of queued triggers"""
        from .models import AutomationTrigger
        
        return AutomationTrigger.objects.filter(
            automation__instagram_account=instagram_account,
            status='queued'
        ).count()


# ============================================================================
# MAIN PROCESSING TASK (WITH RATE LIMITING)
# ============================================================================

@shared_task(bind=True, max_retries=3, soft_time_limit=300)
def process_automation_trigger_async(self, trigger_id):
    """
    Process automation trigger with rate limiting
    
    Flow:
    1. Check rate limit
    2. Reply to comment (if enabled)
    3. Send DM
    4. Update stats
    """
    try:
        asyncio.run(_process_trigger_with_rate_limit(self, trigger_id))
    except Exception as e:
        logger.error(f'Error processing trigger {trigger_id}: {str(e)}')
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


async def _process_trigger_with_rate_limit(celery_task, trigger_id):
    """Main processing logic with rate limiting"""
    from .models import AutomationTrigger, Contact
    from automations.services.instagram_service_async import InstagramServiceAsync
    from services.ai_service_async import AIServiceAsync
    
    # ═══════════════════════════════════════════════════════════
    # STEP 1: Load trigger
    # ═══════════════════════════════════════════════════════════
    trigger = await AutomationTrigger.objects.select_related(
        'automation',
        'automation__instagram_account'
    ).aget(id=trigger_id)
    
    automation = trigger.automation
    instagram_account = automation.instagram_account
    
    # ═══════════════════════════════════════════════════════════
    # STEP 2: Check rate limits
    # ═══════════════════════════════════════════════════════════
    rate_limiter = InstagramRateLimiter(instagram_account)
    
    # Check 24-hour per-user rule
    if not rate_limiter.can_send_to_user(trigger.instagram_user_id):
        trigger.status = 'skipped'
        trigger.error_message = 'Already sent DM to this user in last 24 hours'
        await trigger.asave()
        logger.info(f'⏭️ Skipping trigger #{trigger.id} - user already messaged')
        return
    
    # Check hourly rate limit
    if not rate_limiter.can_send_dm():
        # QUEUE IT!
        await asyncio.to_thread(QueueManager.queue_trigger, trigger)
        
        queue_size = await asyncio.to_thread(QueueManager.get_queue_size, instagram_account)
        reset_time = rate_limiter.get_reset_time()
        
        logger.warning(
            f'⚠️ Rate limit reached for @{instagram_account.username} '
            f'(200/hour). Trigger #{trigger.id} queued. '
            f'Queue size: {queue_size}. Resets at: {reset_time.strftime("%H:%M")}'
        )
        
        # Notify user via WebSocket
        await notify_trigger_queued(automation, trigger, queue_size, reset_time)
        return
    
    # ═══════════════════════════════════════════════════════════
    # STEP 3: Initialize Instagram service
    # ═══════════════════════════════════════════════════════════
    instagram_service = InstagramServiceAsync(instagram_account.access_token)
    
    trigger.status = 'processing'
    await trigger.asave()
    
    # Notify processing started
    await notify_trigger_processing(automation, trigger)
    
    # ═══════════════════════════════════════════════════════════
    # STEP 4: Reply to comment publicly (if enabled)
    # ═══════════════════════════════════════════════════════════
    comment_reply_success = False
    
    if automation.enable_comment_reply and automation.comment_reply_message:
        if trigger.comment_id:
            # Replace variables in reply message
            reply_message = automation.comment_reply_message.replace(
                '{username}', trigger.instagram_username
            )
            
            # Reply to comment
            reply_result = await instagram_service.reply_to_comment(
                comment_id=trigger.comment_id,
                reply_message=reply_message
            )
            
            if reply_result['success']:
                comment_reply_success = True
                trigger.comment_reply_sent = True
                trigger.comment_reply_text = reply_message
                logger.info(f"✓ Replied to comment from @{trigger.instagram_username}")
            else:
                logger.warning(f"Failed to reply to comment: {reply_result.get('error')}")
    
    # ═══════════════════════════════════════════════════════════
    # STEP 5: Prepare DM message (with AI enhancement)
    # ═══════════════════════════════════════════════════════════
    message = automation.DmMessage
    
    if automation.use_ai_enhancement and automation.ai_context:
        try:
            ai_service = AIServiceAsync()
            
            result = await ai_service.enhance_DmMessage(
                base_message=message,
                business_context=automation.ai_context,
                user_comment=trigger.comment_text,
                username=trigger.instagram_username,
                preferred_provider='openrouter'
            )
            
            if result['success']:
                message = result['enhanced_message']
                trigger.was_ai_enhanced = True
                trigger.ai_modifications = f"{result['provider_used']}/{result['model_used']}"
        except Exception as e:
            logger.error(f'AI enhancement failed: {str(e)}')
            # Continue with original message
    
    # ═══════════════════════════════════════════════════════════
    # STEP 6: Send DM
    # ═══════════════════════════════════════════════════════════
    dm_result = await instagram_service.send_dm(
        recipient_id=trigger.instagram_user_id,
        message=message,
        buttons=automation.dm_buttons
    )
    
    # ═══════════════════════════════════════════════════════════
    # STEP 7: Update records
    # ═══════════════════════════════════════════════════════════
    if dm_result['success']:
        # SUCCESS! Increment rate limit counter
        await asyncio.to_thread(rate_limiter.increment_count)
        await asyncio.to_thread(rate_limiter.mark_user_sent, trigger.instagram_user_id)
        
        trigger.status = 'sent'
        trigger.dm_sent_at = timezone.now()
        trigger.DmMessage_sent = message
        await trigger.asave()
        
        # Update automation stats
        automation.total_dms_sent += 1
        if comment_reply_success:
            automation.total_comment_replies += 1
        automation.last_triggered_at = timezone.now()
        await automation.asave()
        
        # Update contact record
        contact, created = await Contact.objects.aupdate_or_create(
            instagram_account=instagram_account,
            instagram_user_id=trigger.instagram_user_id,
            defaults={
                'instagram_username': trigger.instagram_username,
                'total_interactions': 1 if created else F('total_interactions') + 1,
                'total_dms_received': 1 if created else F('total_dms_received') + 1,
                'last_interaction': timezone.now()
            }
        )
        
        # Notify success
        await notify_dm_sent(automation, trigger, comment_reply_success)
        
        logger.info(
            f'✓ DM sent to @{trigger.instagram_username} '
            f'(Trigger #{trigger.id}). '
            f'Quota remaining: {rate_limiter.get_remaining_quota()}/200'
        )
    else:
        # FAILED
        trigger.status = 'failed'
        trigger.error_message = dm_result.get('error', 'Failed to send DM via Instagram API')
        await trigger.asave()
        
        logger.error(f'✗ Failed to send DM for trigger #{trigger.id}: {trigger.error_message}')
        
        # Retry with exponential backoff
        raise celery_task.retry(countdown=2 ** celery_task.request.retries)


# ============================================================================
# QUEUE PROCESSOR (Runs every hour)
# ============================================================================

@shared_task
def process_queued_triggers():
    """
    Process queued triggers for all accounts
    Runs every hour via Celery Beat
    
    This is how DmMe handles viral posts!
    """
    from .models import InstagramAccount
    
    logger.info('🔄 Processing queued triggers...')
    
    active_accounts = InstagramAccount.objects.filter(is_active=True)
    
    total_processed = 0
    
    for account in active_accounts:
        rate_limiter = InstagramRateLimiter(account)
        remaining_quota = rate_limiter.get_remaining_quota()
        
        if remaining_quota <= 0:
            logger.info(f'⏭️ Skipping @{account.username} - quota exhausted this hour')
            continue
        
        # Get queued triggers (up to remaining quota)
        queued = QueueManager.get_queued_triggers(account, limit=remaining_quota)
        
        if not queued.exists():
            continue
        
        logger.info(
            f'📤 Processing {queued.count()} queued triggers for @{account.username} '
            f'(Quota: {remaining_quota}/200)'
        )
        
        for trigger in queued:
            # Process trigger (will respect rate limit)
            process_automation_trigger_async.delay(str(trigger.id))
            total_processed += 1
    
    logger.info(f'✓ Queue processing complete. Processed {total_processed} triggers.')


# ============================================================================
# WEBSOCKET NOTIFICATIONS
# ============================================================================

async def notify_trigger_processing(automation, trigger):
    """Send WebSocket notification when processing starts"""
    from channels.db import database_sync_to_async
    
    user_id = await database_sync_to_async(
        lambda: automation.instagram_account.user_id
    )()
    
    await channel_layer.group_send(
        f'user_{user_id}',
        {
            'type': 'automation_triggered',
            'automation_id': str(automation.id),
            'trigger_data': {
                'id': str(trigger.id),
                'username': trigger.instagram_username,
                'status': trigger.status
            }
        }
    )


async def notify_trigger_queued(automation, trigger, queue_size, reset_time):
    """Notify when trigger is queued due to rate limit"""
    from channels.db import database_sync_to_async
    
    user_id = await database_sync_to_async(
        lambda: automation.instagram_account.user_id
    )()
    
    await channel_layer.group_send(
        f'user_{user_id}',
        {
            'type': 'trigger_queued',
            'automation_id': str(automation.id),
            'trigger_data': {
                'id': str(trigger.id),
                'username': trigger.instagram_username,
                'queue_position': queue_size,
                'reset_time': reset_time.isoformat()
            }
        }
    )


async def notify_dm_sent(automation, trigger, comment_reply_sent):
    """Notify when DM is sent"""
    from channels.db import database_sync_to_async
    
    user_id = await database_sync_to_async(
        lambda: automation.instagram_account.user_id
    )()
    
    await channel_layer.group_send(
        f'user_{user_id}',
        {
            'type': 'dm_sent',
            'automation_id': str(automation.id),
            'recipient': trigger.instagram_username,
            'status': 'success',
            'comment_reply_sent': comment_reply_sent
        }
    )


# ============================================================================
# COMMENT CHECKING (Optional - if not using webhooks)
# ============================================================================

@shared_task
def check_comments_bulk_async():
    """Check comments across all active automations"""
    asyncio.run(_check_comments_async())


async def _check_comments_async():
    """Check comments and create triggers"""
    from .models import Automation
    
    automations = [
        a async for a in Automation.objects.filter(
            is_active=True,
            trigger_type='comment'
        ).select_related('instagram_account')
    ]
    
    logger.info(f"Checking {len(automations)} automations for new comments")
    
    tasks = [process_automation_comments(automation) for automation in automations]
    await asyncio.gather(*tasks, return_exceptions=True)


async def process_automation_comments(automation):
    """Process comments for a single automation"""
    from .models import AutomationTrigger
    from automations.services.instagram_service_async import InstagramServiceAsync
    
    instagram_service = InstagramServiceAsync(
        automation.instagram_account.access_token
    )
    
    posts_to_check = automation.target_posts if automation.target_posts else []
    
    for post_id in posts_to_check:
        comments = await instagram_service.get_comments(post_id)
        
        for comment in comments:
            # Check if already processed
            cache_key = f"comment_processed_{comment['id']}"
            if await cache.aget(cache_key):
                continue
            
            # Check trigger conditions
            should_trigger = check_trigger_conditions(
                automation,
                comment.get('text', '')
            )
            
            if should_trigger:
                # Create trigger record
                trigger = await AutomationTrigger.objects.acreate(
                    automation=automation,
                    instagram_user_id=comment['from']['id'],
                    instagram_username=comment['from'].get('username', ''),
                    post_id=post_id,
                    comment_id=comment['id'],
                    comment_text=comment['text'],
                    status='pending'
                )
                
                # Mark as processed
                await cache.aset(cache_key, True, 86400)
                
                # Queue for processing
                process_automation_trigger_async.delay(str(trigger.id))
                
                # Update stats
                automation.total_triggers += 1
                await automation.asave()


def check_trigger_conditions(automation, comment_text: str) -> bool:
    """Check if comment matches trigger conditions"""
    comment_lower = comment_text.lower()
    
    if automation.trigger_match_type == 'any':
        return True
    elif automation.trigger_match_type == 'exact':
        return any(
            keyword.lower() == comment_lower
            for keyword in automation.trigger_keywords
        )
    elif automation.trigger_match_type == 'contains':
        return any(
            keyword.lower() in comment_lower
            for keyword in automation.trigger_keywords
        )
    
    return False



# ============================================================================
# ADD TO core/celery.py (Celery Beat Schedule)
# ============================================================================

"""
from celery.schedules import crontab

app.conf.beat_schedule = {
    # Process queued triggers every hour
    'process-queued-triggers': {
        'task': 'automations.tasks.process_queued_triggers',
        'schedule': crontab(minute=0),  # Every hour at :00
    },
    
    # Optional: Check comments every 5 minutes (if not using webhooks)
    # 'check-comments': {
    #     'task': 'automations.tasks.check_comments_bulk_async',
    #     'schedule': crontab(minute='*/5'),
    # },
}
"""