import asyncio
from time import timezone
from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
import logging
from channels.db import database_sync_to_async
from django.db.models import F
from .services.instagram_service_async import InstagramServiceAsync

logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


@shared_task(bind=True, max_retries=3, soft_time_limit=300)
def process_automation_trigger_async(self, trigger_id: str):
    """
    Async task wrapper - runs in Celery worker
    Doesn't block main thread
    """
    try:
        # Run async function in event loop
        asyncio.run(_process_trigger_async(trigger_id))
    except Exception as e:
        logger.error(f"Task failed for trigger {trigger_id}: {str(e)}")
        raise self.retry(exc=e, countdown=60)


async def _process_trigger_async(trigger_id: str):
    """
    Actual async processing logic
    All I/O operations are non-blocking
    """
    from .models import AutomationTrigger, Automation
    from .services.instagram_service_async import InstagramServiceAsync
    from .services.ai_service_async import AIServiceAsync
    from django.utils import timezone
    
    # Async DB access
    trigger = await AutomationTrigger.objects.select_related(
        'automation',
        'automation__instagram_account'
    ).aget(id=trigger_id)
    
    automation = trigger.automation
    
    # Update status
    trigger.status = 'processing'
    await trigger.asave()
    
    # Notify via WebSocket (non-blocking)
    asyncio.create_task(notify_trigger_processing(automation, trigger))
    
    # Check rate limits (using Redis cache - async)
    rate_key = f'rate_limit_{automation.instagram_account.id}'
    current_count = await cache.aget(rate_key, 0)
    
    if current_count > 100:  # Max 100 DMs per hour
        trigger.status = 'skipped'
        trigger.failure_reason = 'Rate limit exceeded'
        await trigger.asave()
        return
    
    # Instagram API calls (async with httpx)
    instagram_service = InstagramServiceAsync(
        automation.instagram_account.access_token
    )
    
    # Check follower status if required (non-blocking)
    if automation.require_follow:
        is_following = await instagram_service.check_if_following(
            automation.instagram_account.instagram_user_id,
            trigger.instagram_user_id
        )
        
        if not is_following:
            await instagram_service.send_dm(
                trigger.instagram_user_id,
                automation.follow_check_message or "Please follow us first!"
            )
            trigger.status = 'skipped'
            trigger.failure_reason = 'User not following'
            await trigger.asave()
            return
    
    # AI Enhancement (async, with retry/fallback)
    message = automation.dm_message
    
    if automation.use_ai_enhancement and automation.ai_context:
        ai_service = AIServiceAsync()
        
        result = await ai_service.enhance_dm_message(
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
    
    # Send DM (async)
    result = await instagram_service.send_dm(
        trigger.instagram_user_id,
        message,
        automation.dm_buttons
    )
    
    if result['success']:
        trigger.status = 'sent'
        trigger.dm_sent_at = timezone.now()
        trigger.dm_message_sent = message
        
        # Update stats
        automation.total_dms_sent += 1
        await automation.asave()
        
        # Increment rate limit
        await cache.aset(rate_key, current_count + 1, 3600)
        
        # Update contact (async)
        await update_contact_async(automation, trigger)
        
        # Notify via WebSocket
        asyncio.create_task(notify_dm_sent(automation, trigger))
    else:
        trigger.status = 'failed'
        trigger.failure_reason = result.get('error', 'Unknown error')
    
    await trigger.asave()


async def notify_trigger_processing(automation, trigger):
    """Send WebSocket notification (non-blocking)"""
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


async def notify_dm_sent(automation, trigger):
    """Notify when DM is successfully sent"""
    user_id = await database_sync_to_async(
        lambda: automation.instagram_account.user_id
    )()
    
    await channel_layer.group_send(
        f'user_{user_id}',
        {
            'type': 'dm_sent',
            'automation_id': str(automation.id),
            'recipient': trigger.instagram_username,
            'status': 'success'
        }
    )


@shared_task
def check_comments_bulk_async():
    """
    Bulk comment checking - runs every 30 seconds
    Handles 1000s of posts concurrently
    """
    asyncio.run(_check_comments_async())


async def _check_comments_async():
    """
    Check comments across all active automations
    Fully async, processes 100+ posts concurrently
    """
    from .models import Automation
    from .services.instagram_service_async import InstagramServiceAsync
    
    # Get all active automations
    automations = [
        a async for a in Automation.objects.filter(
            is_active=True,
            trigger_type='comment'
        ).select_related('instagram_account')
    ]
    
    logger.info(f"Checking {len(automations)} automations for new comments")
    
    # Process all automations concurrently
    tasks = [process_automation_comments(automation) for automation in automations]
    await asyncio.gather(*tasks, return_exceptions=True)


async def process_automation_comments(automation):
    """Process comments for a single automation"""
    from .models import AutomationTrigger
    
    instagram_service = InstagramServiceAsync(
        automation.instagram_account.access_token
    )
    
    posts_to_check = automation.target_posts if automation.target_posts else []
    
    # Process all posts concurrently
    for post_id in posts_to_check:
        comments = await instagram_service.get_comments(post_id)
        
        for comment in comments:
            # Check if already processed (async cache check)
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
                await cache.aset(cache_key, True, 86400)  # 24 hours
                
                # Queue for processing (non-blocking)
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


async def update_contact_async(automation, trigger):
    """Update contact record asynchronously"""
    from .models import Contact
    
    contact, created = await Contact.objects.aupdate_or_create(
        instagram_account=automation.instagram_account,
        instagram_user_id=trigger.instagram_user_id,
        defaults={
            'instagram_username': trigger.instagram_username,
            'total_interactions': 1 if created else F('total_interactions') + 1,
            'total_dms_received': 1 if created else F('total_dms_received') + 1,
            'last_interaction': timezone.now()
        }
    )

