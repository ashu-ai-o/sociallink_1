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
        logger.info('✓ Webhook verified successfully')
        return HttpResponse(challenge, content_type='text/plain')
    else:
        logger.error('✗ Webhook verification failed')
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
        logger.warning('Missing signature in webhook request')
        return False
    
    # Remove 'sha256=' prefix
    signature = signature.replace('sha256=', '')
    
    # Calculate expected signature
    expected_signature = hmac.new(
        key=settings.FACEBOOK_APP_SECRET.encode('utf-8'),
        msg=request.body,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    # Compare signatures
    if not hmac.compare_digest(signature, expected_signature):
        logger.error('Webhook signature verification failed')
        return False
    
    return True


# ============================================================================
# WEBHOOK EVENT HANDLER
# ============================================================================

def handle_webhook(request):
    """
    Process incoming webhook events from Instagram
    
    Events include:
    - Comments on posts
    - Direct messages
    - Story mentions
    - Story replies
    """
    
    # Verify signature
    if not verify_signature(request):
        return JsonResponse({'error': 'Invalid signature'}, status=403)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        logger.info(f'Received webhook: {json.dumps(data, indent=2)}')
        
        # Process each entry
        for entry in data.get('entry', []):
            process_entry(entry)
        
        return JsonResponse({'status': 'success'}, status=200)
        
    except json.JSONDecodeError:
        logger.error('Invalid JSON in webhook payload')
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f'Webhook processing error: {str(e)}')
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
    
    # Get Instagram account from database
    try:
        instagram_account = InstagramAccount.objects.get(
            instagram_user_id=instagram_account_id,
            is_active=True
        )
    except InstagramAccount.DoesNotExist:
        logger.warning(f'Instagram account {instagram_account_id} not found')
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
    
    logger.info(f'📝 New comment from @{username}: "{comment_text}"')
    
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
            
            logger.info(f'✓ Created trigger {trigger.id} for automation {automation.name}')
            
            # Process in background (Celery task)
            process_automation_trigger_async.delay(str(trigger.id))
            
            # Update automation stats
            automation.total_triggers += 1
            automation.save()


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
            process_automation_trigger_async.delay(str(trigger.id))

