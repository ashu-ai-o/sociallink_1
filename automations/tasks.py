"""
Celery Tasks - WITH COMMENT REPLY FEATURE
Replies to comments publicly + sends DM privately
"""

import asyncio
from celery import shared_task
from channels.layers import get_channel_layer
from django.core.cache import cache
from django.utils import timezone
from django.db.models import F
import logging

from automations.services.instagram_service_async import InstagramServiceAsync

logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


@shared_task(bind=True, max_retries=3, soft_time_limit=300)
def process_automation_trigger_async(self, trigger_id: str):
    """
    Process trigger: Reply to comment + Send DM
    """
    try:
        asyncio.run(_process_trigger_async(trigger_id))
    except Exception as e:
        logger.error(f"Task failed for trigger {trigger_id}: {str(e)}")
        raise self.retry(exc=e, countdown=60)


async def _process_trigger_async(trigger_id: str):
    """
    NEW FLOW:
    1. Reply to comment publicly (if enabled)
    2. Send DM privately
    """
    from .models import AutomationTrigger, Automation
    from .services.instagram_service_async import InstagramServiceAsync
    from .services.ai_service_async import AIServiceAsync
    
    # ═══════════════════════════════════════════════════════════
    # STEP 1: Load trigger data
    # ═══════════════════════════════════════════════════════════
    trigger = await AutomationTrigger.objects.select_related(
        'automation',
        'automation__instagram_account'
    ).aget(id=trigger_id)
    
    automation = trigger.automation
    
    # Update status
    trigger.status = 'processing'
    await trigger.asave()
    
    # Notify via WebSocket
    asyncio.create_task(notify_trigger_processing(automation, trigger))
    
    # ═══════════════════════════════════════════════════════════
    # STEP 2: Check rate limits
    # ═══════════════════════════════════════════════════════════
    rate_key = f'rate_limit_{automation.instagram_account.id}'
    current_count = await cache.aget(rate_key, 0)
    
    if current_count > 100:
        trigger.status = 'skipped'
        trigger.failure_reason = 'Rate limit exceeded'
        await trigger.asave()
        return
    
    # ═══════════════════════════════════════════════════════════
    # STEP 3: Initialize Instagram service
    # ═══════════════════════════════════════════════════════════
    instagram_service = InstagramServiceAsync(
        automation.instagram_account.access_token
    )
    
    # ═══════════════════════════════════════════════════════════
    # STEP 4: NEW! Reply to comment publicly (if enabled)
    # ═══════════════════════════════════════════════════════════
    
    comment_reply_success = False
    
    if automation.enable_comment_reply and automation.comment_reply_message:
        if trigger.comment_id:  # Only if we have a comment ID
            
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
                # Continue anyway - DM is more important
    
    # ═══════════════════════════════════════════════════════════
    # STEP 5: Prepare DM message (with optional AI enhancement)
    # ═══════════════════════════════════════════════════════════
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
    
    # ═══════════════════════════════════════════════════════════
    # STEP 6: Send DM
    # ═══════════════════════════════════════════════════════════
    result = await instagram_service.send_dm(
        trigger.instagram_user_id,
        message,
        automation.dm_buttons
    )
    
    # ═══════════════════════════════════════════════════════════
    # STEP 7: Update records
    # ═══════════════════════════════════════════════════════════
    if result['success']:
        trigger.status = 'sent'
        trigger.dm_sent_at = timezone.now()
        trigger.dm_message_sent = message
        
        # Update stats
        automation.total_dms_sent += 1
        if comment_reply_success:
            automation.total_comment_replies += 1
        await automation.asave()
        
        # Increment rate limit
        await cache.aset(rate_key, current_count + 1, 3600)
        
        # Update contact
        await update_contact_async(automation, trigger)
        
        # Notify via WebSocket
        asyncio.create_task(notify_dm_sent(automation, trigger, comment_reply_success))
    else:
        trigger.status = 'failed'
        trigger.failure_reason = result.get('error', 'Unknown error')
    
    await trigger.asave()


async def notify_trigger_processing(automation, trigger):
    """Send WebSocket notification"""
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
            'comment_reply_sent': comment_reply_sent  # NEW!
        }
    )


async def update_contact_async(automation, trigger):
    """Update contact record"""
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


@shared_task
def check_comments_bulk_async():
    """Check comments across all active automations"""
    asyncio.run(_check_comments_async())


async def _check_comments_async():
    """Check comments and create triggers"""
    from .models import Automation
    from .services.instagram_service_async import InstagramServiceAsync
    
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
                    comment_id=comment['id'],  # IMPORTANT: Save comment ID!
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


# ═══════════════════════════════════════════════════════════════
# SUMMARY OF NEW FEATURES:
# ═══════════════════════════════════════════════════════════════
#
# ✅ ADDED: Comment reply functionality (Step 4)
# ✅ ADDED: comment_reply_success tracking
# ✅ ADDED: WebSocket notification includes comment_reply_sent
# ✅ ADDED: automation.total_comment_replies counter
#
# New Flow:
# 1. Load trigger
# 2. Check rate limits
# 3. Initialize Instagram service
# 4. Reply to comment publicly (NEW!)
# 5. AI enhance DM message
# 6. Send DM privately
# 7. Update records
#
# ═══════════════════════════════════════════════════════════════