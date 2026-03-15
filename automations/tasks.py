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
# QUEUE ROUTING HELPER
# ============================================================================

def _get_user_queue(instagram_account) -> str:
    """
    Return the correct Celery queue name based on the user's subscription plan.

    Paid (pro / business, status=active) → 'paid_high'  (fast workers)
    Free or inactive subscription        → 'free_default'

    Source: payments.models.UserSubscription + SubscriptionPlan
      - user.subscription.plan.name  → 'free' | 'pro' | 'business'
      - user.subscription.status     → 'active' | 'trial' | 'cancelled' | 'expired' | 'suspended'
    """
    PAID_PLANS = {'pro', 'business'}
    ACTIVE_STATUSES = {'active'}   # trial users stay on free_default

    try:
        subscription = instagram_account.user.subscription  # OneToOne from UserSubscription
        plan_name = subscription.plan.name          # 'free' | 'pro' | 'business'
        status    = subscription.status             # 'active' | 'trial' | etc.

        is_paid = plan_name in PAID_PLANS and status in ACTIVE_STATUSES
        return 'paid_high' if is_paid else 'free_default'

    except Exception:
        # User has no subscription row yet → treat as free
        return 'free_default'


def dispatch_trigger(trigger) -> None:
    """
    Dispatch a trigger to the correct Celery queue based on the user's plan.
    Use this instead of calling process_automation_trigger_async.delay() directly.
    """
    queue = _get_user_queue(trigger.automation.instagram_account)
    process_automation_trigger_async.apply_async(
        args=[str(trigger.id)],
        queue=queue,
    )
    logger.info(f'[dispatch] Trigger #{trigger.id} → queue={queue}')


# ============================================================================
# MAIN PROCESSING TASK (WITH RATE LIMITING)
# ============================================================================

@shared_task
def refresh_instagram_tokens():
    """
    Automatically refresh Instagram Platform API tokens that are expiring soon.
    
    Tokens last ~60 days. This task runs daily and refreshes any token that
    expires in less than 15 days, keeping automations running continuously.
    
    Only refreshes 'instagram_platform' tokens (graph.instagram.com).
    Facebook Graph API tokens are tied to Facebook Pages and don't use this flow.
    """
    import requests
    from accounts.models import InstagramAccount
    from django.utils import timezone
    from datetime import timedelta

    threshold = timezone.now() + timedelta(days=15)

    # Find platform tokens expiring within 15 days
    expiring = InstagramAccount.objects.filter(
        connection_method='instagram_platform',
        is_active=True,
        token_expires_at__lte=threshold,
    )

    count = expiring.count()
    if count == 0:
        logger.info('[token_refresh] All Instagram tokens are healthy (>15 days remaining)')
        return

    logger.info(f'[token_refresh] Found {count} token(s) expiring within 15 days — refreshing...')

    for account in expiring:
        try:
            resp = requests.get(
                'https://graph.instagram.com/refresh_access_token',
                params={
                    'grant_type': 'ig_refresh_token',
                    'access_token': account.access_token,
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()

            new_token = data.get('access_token')
            expires_in = data.get('expires_in', 5184000)  # default ~60 days

            if new_token:
                account.access_token = new_token
                account.token_expires_at = timezone.now() + timedelta(seconds=expires_in)
                account.save(update_fields=['access_token', 'token_expires_at'])
                logger.info(
                    f'[token_refresh] ✓ Refreshed token for @{account.username} — '
                    f'valid until {account.token_expires_at.strftime("%Y-%m-%d")}'
                )
            else:
                logger.error(
                    f'[token_refresh] ✗ No new token in response for @{account.username}: {data}'
                )
        except Exception as e:
            logger.error(
                f'[token_refresh] ✗ Failed to refresh token for @{account.username}: {e}'
            )


@shared_task
def retry_pending_triggers():
    """
    Periodic safety net: dispatch any triggers stuck in 'pending' status.
    Runs every 30 seconds via Celery Beat.
    """
    from .models import AutomationTrigger
    from django.utils import timezone

    # Only retry triggers < 24 hours old
    cutoff = timezone.now() - timezone.timedelta(hours=24)
    pending = AutomationTrigger.objects.filter(
        status='pending',
        created_at__gte=cutoff
    ).order_by('created_at')

    count = pending.count()

    # Always log a heartbeat so Celery shows it's alive
    total_sent = AutomationTrigger.objects.filter(status='sent').count()
    total_failed = AutomationTrigger.objects.filter(status='failed').count()
    total_processing = AutomationTrigger.objects.filter(status='processing').count()
    logger.info(
        f'[BEAT] Celery alive | pending={count} processing={total_processing} '
        f'sent={total_sent} failed={total_failed}'
    )

    if count == 0:
        return

    logger.info(f'[retry_pending_triggers] Found {count} pending triggers — dispatching...')
    dispatched = 0
    for trigger in pending:
        try:
            process_automation_trigger_async.delay(str(trigger.id))
            dispatched += 1
        except Exception as e:
            logger.error(f'[retry_pending_triggers] Failed to dispatch trigger {trigger.id}: {e}')

    logger.info(f'[retry_pending_triggers] Dispatched {dispatched}/{count} triggers')


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

    Queue routing:
    - Paid users: dispatched to 'paid_high' queue
    - Free users: dispatched to 'free_default' queue
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
    from automations.services.ai_service_async import AIServiceOpenRouter
    from automations.services.gemini_service_async import AIServiceGemini
    from automations.models import AISettings
    
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
    instagram_service = InstagramServiceAsync(
        instagram_account.access_token,
        connection_method=instagram_account.connection_method
    )
    
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
            # Skip reply for simulated / test comment IDs (local dev testing)
            is_simulated = str(trigger.comment_id).startswith('SIMULATED_')
            if is_simulated:
                logger.info(
                    f'[DEV] Skipping comment reply for simulated comment_id={trigger.comment_id}'
                )
            else:
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
        if trigger.ai_modifications == 'FAILED':
            logger.info(f"Skipping AI enhancement for trigger #{trigger.id} due to previous failure.")
        else:
            try:
                from django.conf import settings as django_settings
                ai_settings = AISettings.load()
                
                # Check active provider
                if ai_settings.provider == 'gemini':
                    ai_service = AIServiceGemini()
                else:
                    api_key = getattr(django_settings, 'OPENROUTER_API_KEY', '')
                    # Instantiate openrouter pool or single key
                    ai_service = AIServiceOpenRouter()

                if ai_service:
                    result = await ai_service.enhance_DmMessage(
                        base_message=message,
                        business_context=automation.ai_context,
                        user_comment=trigger.comment_text,
                        username=trigger.instagram_username,
                    )
                    if result['success']:
                        message = result['enhanced_message']
                        trigger.was_ai_enhanced = True
                        trigger.ai_modifications = result.get('model_used', ai_settings.provider)
                    else:
                        logger.warning(f"AI Enhancement failed for trigger #{trigger.id}. Flagging to avoid retries.")
                        trigger.was_ai_enhanced = False
                        trigger.ai_modifications = 'FAILED'
                        await trigger.asave(update_fields=['was_ai_enhanced', 'ai_modifications'])
                    await ai_service.close()
            except Exception as e:
                logger.error(f'AI enhancement failed: {str(e)}')
                trigger.was_ai_enhanced = False
                trigger.ai_modifications = 'FAILED'
                await trigger.asave(update_fields=['was_ai_enhanced', 'ai_modifications'])
                # Continue with original message
    
    # ═══════════════════════════════════════════════════════════
    # STEP 6: Send DM
    # ═══════════════════════════════════════════════════════════
    dm_result = await instagram_service.send_dm(
        recipient_id=trigger.instagram_user_id,
        message=message,
        buttons=automation.dm_buttons,
        comment_id=trigger.comment_id or None,
        ig_user_id=instagram_account.platform_id or instagram_account.instagram_user_id,
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
        # NOTE: 'created' cannot be used inside defaults — it's only assigned after
        # aupdate_or_create returns. Use a two-step approach instead.
        contact, contact_created = await Contact.objects.aupdate_or_create(
            instagram_account=instagram_account,
            instagram_user_id=trigger.instagram_user_id,
            defaults={
                'instagram_username': trigger.instagram_username,
                'last_interaction': timezone.now()
            }
        )
        # Increment counters now that we know whether the record is new or existing
        if contact_created:
            contact.total_interactions = 1
            contact.total_dms_received = 1
            await contact.asave(update_fields=['total_interactions', 'total_dms_received'])
        else:
            await Contact.objects.filter(id=contact.id).aupdate(
                total_interactions=F('total_interactions') + 1,
                total_dms_received=F('total_dms_received') + 1,
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

        error_subcode = dm_result.get('error_subcode')
        error_code = dm_result.get('error_code')

        # ── Permanent errors: retrying will never help ──────────────────────
        # subcode 2534014 = IGSID/user not found (user not accessible to app)
        # subcode 2018034 = User has disabled receiving messages
        # subcode 2018001 = App not authorized to message this user
        # subcode   551   = User cannot receive messages
        PERMANENT_SUBCODES = {2534014, 2018034, 2018001, 551}

        if error_subcode in PERMANENT_SUBCODES:
            logger.error(
                f'✗ Trigger #{trigger.id} failed with permanent Instagram error '
                f'(code={error_code}, subcode={error_subcode}). Not retrying. '
                f'In development mode ensure the recipient is added as a Test User '
                f'in your Meta App and has granted instagram_business_manage_messages permission.'
            )
            return
        # ────────────────────────────────────────────────────────────────────

        logger.error(f'✗ Failed to send DM for trigger #{trigger.id}: {trigger.error_message}')

        # Retry with exponential backoff — max 3 retries to avoid infinite retry storms
        if celery_task.request.retries < 3:
            raise celery_task.retry(countdown=2 ** celery_task.request.retries)
        else:
            logger.error(f'✗ Trigger #{trigger.id} exceeded max retries (3). Giving up.')


# ============================================================================
# QUEUE-AWARE DISPATCH HELPER
# ============================================================================

def dispatch_trigger(trigger) -> None:
    """
    Dispatch a trigger to the correct Celery queue based on the user's plan.
    Call this wherever you previously called process_automation_trigger_async.delay().
    """
    queue = _get_user_queue(trigger.automation.instagram_account)
    process_automation_trigger_async.apply_async(
        args=[str(trigger.id)],
        queue=queue,
    )
    logger.info(f'[dispatch] Trigger #{trigger.id} → queue={queue}')


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

    account = automation.instagram_account
    instagram_service = InstagramServiceAsync(
        account.access_token,
        connection_method=account.connection_method
    )

    posts_to_check = automation.target_posts if automation.target_posts else []

    logger.info(
        f'[POLL] automation="{automation.name}" | '
        f'account=@{account.username} | '
        f'connection_method={account.connection_method} | '
        f'token_snippet={account.access_token[:15]}... | '
        f'target_posts={posts_to_check}'
    )

    if not posts_to_check:
        logger.warning(
            f'[POLL] automation="{automation.name}" has no target_posts — nothing to poll. '
            f'Add a post ID in the automation settings.'
        )
        return

    for post_id in posts_to_check:
        comments = await instagram_service.get_comments(post_id)

        logger.info(
            f'[POLL] post={post_id} | automation="{automation.name}" | '
            f'found {len(comments)} comments from API'
        )

        for comment in comments:
            comment_id = comment.get('id')
            if not comment_id:
                continue

            # Check if already processed
            cache_key = f"comment_processed_{comment_id}"
            if await cache.aget(cache_key):
                continue
            
            # Check trigger conditions
            comment_text = comment.get('text', '')
            should_trigger = check_trigger_conditions(automation, comment_text)
            
            if not should_trigger:
                logger.info(
                    f'[POLL] comment "{comment_text}" did not match '
                    f'automation "{automation.name}" (keywords={automation.trigger_keywords}, '
                    f'match_type={automation.trigger_match_type}) — skipping'
                )
                # Still mark as checked so we don't re-evaluate every 30s
                await cache.aset(cache_key, 'skipped', 86400)
                continue

            # Get user info from comment — Instagram Platform API sometimes omits 'from'
            from_data = comment.get('from', {})
            user_id = from_data.get('id') or ''  # May be empty for MEDIA_CREATOR accounts
            username = from_data.get('username') or comment.get('username') or ''

            logger.info(
                f'[POLL] ✓ MATCH: comment_id={comment_id} | '
                f'@{username}(id={user_id!r}) | text="{comment_text}"'
            )

            # Create trigger record
            # When user_id is missing, store the comment_id in instagram_user_id field
            # so the DM task can use comment_id as recipient (Instagram allows this)
            trigger = await AutomationTrigger.objects.acreate(
                automation=automation,
                instagram_user_id=user_id or f'comment:{comment_id}',
                instagram_username=username,
                post_id=post_id,
                comment_id=comment_id,
                comment_text=comment_text,
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