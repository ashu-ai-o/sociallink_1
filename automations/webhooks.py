from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
import hmac
import hashlib
import json
import logging
from .models import Automation, AutomationTrigger, InstagramAccount
from .tasks import process_automation_trigger_async

logger = logging.getLogger(__name__)


# ============================================================================
# WEBHOOK VERIFICATION
# ============================================================================

@csrf_exempt
@require_http_methods(["GET", "POST"])
def instagram_webhook(request):
    """
    Main webhook endpoint for Instagram events
    
    Handles:
    - GET: Webhook verification
    - POST: Incoming webhook events
    
    Endpoint: /api/webhooks/instagram/
    """
    
    if request.method == "GET":
        return verify_webhook(request)
    elif request.method == "POST":
        return handle_webhook(request)


def verify_webhook(request):
    """
    Step 1: Verify webhook subscription
    
    Instagram sends GET request with:
    - hub.mode = "subscribe"
    - hub.challenge = random string
    - hub.verify_token = your token
    
    You must return hub.challenge to verify
    """
    mode = request.GET.get('hub.mode')
    token = request.GET.get('hub.verify_token')
    challenge = request.GET.get('hub.challenge')
    
    # Verify token matches (set in Meta Developer settings)
    if mode == 'subscribe' and token == settings.INSTAGRAM_WEBHOOK_VERIFY_TOKEN:
        logger.info('Webhook verified successfully')
        return HttpResponse(challenge, content_type='text/plain')
    else:
        logger.error('Webhook verification failed')
        return HttpResponse('Verification token mismatch', status=403)


# ============================================================================
# WEBHOOK SIGNATURE VERIFICATION
# ============================================================================

def verify_signature(request):
    """
    Verify webhook signature to ensure request is from Instagram
    
    Instagram signs requests with HMAC-SHA256
    """
    signature = request.headers.get('X-Hub-Signature-256', '')
    
    if not signature:
        logger.warning('[WARNING] Webhook rejected: Missing X-Hub-Signature-256 header')
        return False
    
    # Remove 'sha256=' prefix
    signature_hash = signature.replace('sha256=', '')
    
    # [DEBUG BYPASS] Allow 'any' signature for local testing
    if settings.DEBUG and signature_hash == 'any':
        logger.info('🛠️ Webhook signature bypassed (DEBUG mode + "any" signature)')
        return True
    
    # Calculate expected signatures
    # We use these settings to verify the request came from Meta/Instagram
    fb_secret = getattr(settings, 'FACEBOOK_APP_SECRET', '')
    ig_secret = getattr(settings, 'INSTAGRAM_CLIENT_SECRET', '')

    if not fb_secret and not ig_secret:
        logger.error('[ERROR] Configuration error: Both FACEBOOK_APP_SECRET and INSTAGRAM_CLIENT_SECRET are empty')
        return False

    expected_facebook_signature = hmac.new(
        key=fb_secret.encode('utf-8'),
        msg=request.body,
        digestmod=hashlib.sha256
    ).hexdigest() if fb_secret else None

    expected_instagram_signature = hmac.new(
        key=ig_secret.encode('utf-8'),
        msg=request.body,
        digestmod=hashlib.sha256
    ).hexdigest() if ig_secret else None
    
    # Compare signatures
    is_valid = False
    if expected_facebook_signature and hmac.compare_digest(signature_hash, expected_facebook_signature):
        logger.info('[SUCCESS] Webhook signature verified using FACEBOOK_APP_SECRET')
        is_valid = True
    elif expected_instagram_signature and hmac.compare_digest(signature_hash, expected_instagram_signature):
        logger.info('[SUCCESS] Webhook signature verified using INSTAGRAM_CLIENT_SECRET')
        is_valid = True

    if not is_valid:
        logger.error(f'[ERROR] Webhook signature verification failed. Provided: {signature_hash[:10]}...')
        return False
    
    return True


# ============================================================================
# WEBHOOK EVENT HANDLER
# ============================================================================

def handle_webhook(request):
    """
    Process incoming webhook events from Instagram
    """
    logger.info(f'[WEBHOOK] Received: {request.method} request to {request.path}')
    
    # 1. Verify signature
    if not verify_signature(request):
        return JsonResponse({'error': 'Invalid signature'}, status=403)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        logger.info(f'[WEBHOOK] Payload: {json.dumps(data, indent=2)}')
        
        # 2. Extract entries
        entries = data.get('entry', [])
        if not entries:
            logger.warning('[WARNING] Webhook contained no entries')
            return JsonResponse({'status': 'no_entries'}, status=200)

        logger.info(f'[PROCESS] Processing {len(entries)} webhook entries...')
        
        # 3. Process each entry
        for entry in entries:
            process_entry(entry)
        
        return JsonResponse({'status': 'success'}, status=200)
        
    except json.JSONDecodeError:
        logger.error('[ERROR] Invalid JSON in webhook payload')
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f'[ERROR] Webhook processing error: {str(e)}', exc_info=True)
        return JsonResponse({'error': 'Processing failed'}, status=500)


# ============================================================================
# ENTRY PROCESSOR
# ============================================================================

def process_entry(entry):
    """
    Process a single webhook entry
    
    Entry structure:
    {
        "id": "instagram_account_id",
        "time": 1234567890,
        "changes": [...]  # or "messaging": [...]
    }
    """
    instagram_account_id = entry.get('id')

    # entry.id maps to different fields depending on connection method:
    #   facebook_graph  — comments  → instagram_user_id
    #   facebook_graph  — DMs       → page_id
    #   instagram_platform — all    → platform_id
    # Try all three so no webhook is silently dropped regardless of connection type.
    instagram_account = (
        InstagramAccount.objects.filter(instagram_user_id=instagram_account_id, is_active=True).first()
        or InstagramAccount.objects.filter(platform_id=instagram_account_id, is_active=True).first()
        or InstagramAccount.objects.filter(page_id=instagram_account_id, is_active=True).first()
    )

    if not instagram_account:
        logger.warning(
            f'Instagram account not found for entry id {instagram_account_id} '
            f'(tried instagram_user_id, platform_id, page_id)'
        )
        return
    
    # Process changes (comments, etc.)
    if 'changes' in entry:
        for change in entry['changes']:
            process_change(change, instagram_account)
    
    # Process messaging events (DMs, story replies)
    if 'messaging' in entry:
        for message in entry['messaging']:
            process_message(message, instagram_account)


# ============================================================================
# COMMENT PROCESSOR
# ============================================================================

def process_change(change, instagram_account):
    """
    Process comment changes
    
    Change structure:
    {
        "field": "comments",
        "value": {
            "media_id": "123",
            "comment_id": "456",
            "text": "link please",
            "from": {
                "id": "789",
                "username": "john_doe"
            }
        }
    }
    """
    field = change.get('field')
    value = change.get('value', {})
    
    if field == 'comments':
        handle_comment(value, instagram_account)


def handle_comment(comment_data, instagram_account):
    """
    Handle new comment on post
    
    This is where automation magic happens!
    """
    media_id = comment_data.get('media_id')
    comment_id = comment_data.get('id')
    comment_text = comment_data.get('text', '')
    from_user = comment_data.get('from', {})
    user_id = from_user.get('id')
    username = from_user.get('username', '')
    
    logger.info(f'[COMMENT] New comment from @{username}: "{comment_text}"')
    
    # Find matching automations
    automations = Automation.objects.filter(
        instagram_account=instagram_account,
        is_active=True,
        trigger_type='comment'
    )
    
    for automation in automations:
        # Check if comment matches triggers
        if should_trigger_automation(automation, comment_text, media_id):
            # Create trigger record
            trigger = AutomationTrigger.objects.create(
                automation=automation,
                instagram_user_id=user_id,
                instagram_username=username,
                post_id=media_id,
                comment_id=comment_id,
                comment_text=comment_text,
                status='pending'
            )
            
            logger.info(f'[TRIGGER] Created trigger {trigger.id} for automation {automation.name}')
            
            # Dispatch to Celery (wrapped — webhook must return 200 even if broker is down)
            try:
                process_automation_trigger_async.delay(str(trigger.id))
                logger.info(f'[TRIGGER] Task queued for trigger {trigger.id}')
            except Exception as celery_err:
                # Don't let Celery failure crash the webhook — trigger stays 'pending'
                # and can be retried later via process_queued_triggers
                logger.error(
                    f'[TRIGGER] Failed to queue Celery task for trigger {trigger.id}: {celery_err}. '
                    f'Trigger saved as pending — will retry when broker is available.'
                )
            
            # Update automation stats (must happen regardless of Celery result)
            try:
                automation.total_triggers += 1
                automation.save(update_fields=['total_triggers'])
            except Exception as save_err:
                logger.error(f'[TRIGGER] Failed to update automation stats: {save_err}')




def should_trigger_automation(automation, comment_text, post_id):
    """
    Check if comment should trigger automation
    
    Checks:
    1. Target posts (if specified)
    2. Trigger keywords
    3. Match type (exact, contains, any)
    """
    # Check target posts
    if automation.target_posts and post_id not in automation.target_posts:
        return False
    
    # Check keywords
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
# MESSAGE PROCESSOR (DMs, Story Replies)
# ============================================================================

def process_message(message, instagram_account):
    """
    Process direct message or story reply
    
    Message structure:
    {
        "sender": {"id": "123"},
        "recipient": {"id": "456"},
        "timestamp": 1234567890,
        "message": {
            "mid": "msg_id",
            "text": "Hello"
        }
    }
    """
    sender = message.get('sender', {})
    msg_data = message.get('message', {})
    
    sender_id = sender.get('id')
    text = msg_data.get('text', '')

    # Ignore echo messages — these are messages the account sent (echoed back by Instagram)
    if sender_id == instagram_account.instagram_user_id:
        logger.debug(f'[DM] Ignoring echo message from own account {sender_id}')
        return

    # Handle story mentions
    if 'story_mention' in msg_data:
        handle_story_mention(sender_id, msg_data, instagram_account)
    
    # Handle story replies
    elif 'reply_to' in msg_data:
        handle_story_reply(sender_id, text, msg_data, instagram_account)
    
    # Handle regular DM keywords
    elif text:
        handle_dm_keyword(sender_id, text, instagram_account)


def handle_story_mention(sender_id, msg_data, instagram_account):
    """Handle @mention in story"""
    logger.info(f'📱 Story mention from user {sender_id}')
    
    automations = Automation.objects.filter(
        instagram_account=instagram_account,
        is_active=True,
        trigger_type='story_mention'
    )
    
    for automation in automations:
        # Create trigger and process
        trigger = AutomationTrigger.objects.create(
            automation=automation,
            instagram_user_id=sender_id,
            comment_text='Story mention',
            status='pending'
        )
        process_automation_trigger_async.delay(str(trigger.id))


def handle_story_reply(sender_id, text, msg_data, instagram_account):
    """Handle reply to story"""
    logger.info(f'💬 Story reply from user {sender_id}: "{text}"')
    
    automations = Automation.objects.filter(
        instagram_account=instagram_account,
        is_active=True,
        trigger_type='story_reply'
    )
    
    for automation in automations:
        if should_trigger_automation(automation, text, None):
            trigger = AutomationTrigger.objects.create(
                automation=automation,
                instagram_user_id=sender_id,
                comment_text=text,
                status='pending'
            )
            process_automation_trigger_async.delay(str(trigger.id))


def handle_dm_keyword(sender_id, text, instagram_account):
    """Handle DM with keyword trigger"""
    logger.info(f'✉️ DM from user {sender_id}: "{text}"')

    automations = Automation.objects.filter(
        instagram_account=instagram_account,
        is_active=True,
        trigger_type='dm_keyword'
    )

    for automation in automations:
        if should_trigger_automation(automation, text, None):
            trigger = AutomationTrigger.objects.create(
                automation=automation,
                instagram_user_id=sender_id,
                comment_text=text,
                status='pending'
            )

            try:
                process_automation_trigger_async.delay(str(trigger.id))
                logger.info(f'[TRIGGER] Task queued for DM trigger {trigger.id}')
            except Exception as celery_err:
                logger.error(
                    f'[TRIGGER] Failed to queue Celery task for DM trigger {trigger.id}: {celery_err}. '
                    f'Trigger saved as pending — will retry when broker is available.'
                )

            try:
                automation.total_triggers += 1
                automation.save(update_fields=['total_triggers'])
            except Exception as save_err:
                logger.error(f'[TRIGGER] Failed to update automation stats: {save_err}')

