"""
Full end-to-end test:
1. Create a REAL comment on the post using wanderwithraconz API token
2. Get the real comment_id from the response
3. Deliver a webhook payload with that real comment_id
4. Watch the DM attempt
"""
import django, os, requests, json, hmac, hashlib, time
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings
from accounts.models import InstagramAccount
from automations.models import Automation, AutomationTrigger

# Load accounts
main = InstagramAccount.objects.filter(username='wanderwithraconz', is_active=True).first()
raconz = InstagramAccount.objects.filter(username='the_raconz', is_active=True).first()

TOKEN = main.access_token
IG_ID = main.platform_id      # 25831541729844493
RACONZ_ID = raconz.instagram_user_id  # 26159303547039775

# Get post from automation
auto = Automation.objects.filter(instagram_account=main, is_active=True).first()
POST_ID = auto.target_posts[0] if auto.target_posts else '18148423327459502'

print(f"Account : @{main.username} (id={IG_ID})")
print(f"Post    : {POST_ID}")
print(f"Raconz  : @{raconz.username} (id={RACONZ_ID})")
print(f"Keyword : {auto.trigger_keywords}")
print()

# ── STEP 1: Create a real comment on the post ─────────────────────────────────
print("=== STEP 1: Creating real comment on post via API ===")
create_resp = requests.post(
    f'https://graph.instagram.com/v25.0/{POST_ID}/comments',
    headers={'Authorization': f'Bearer {TOKEN}'},
    json={'message': 'test1'}
)
print(f"Create comment response: {create_resp.status_code}")
create_data = create_resp.json()
print(json.dumps(create_data, indent=2))

if not create_resp.ok:
    print("\nFailed to create comment. Checking error...")
    err = create_data.get('error', {})
    print(f"code={err.get('code')} subcode={err.get('error_subcode')} msg={err.get('message')}")
    
    # Try with access_token param instead
    print("\nRetrying with access_token param...")
    create_resp2 = requests.post(
        f'https://graph.instagram.com/v25.0/{POST_ID}/comments',
        params={'access_token': TOKEN, 'message': 'test1'}
    )
    print(f"Status: {create_resp2.status_code}")
    print(json.dumps(create_resp2.json(), indent=2))
    create_data = create_resp2.json()

REAL_COMMENT_ID = create_data.get('id')
if not REAL_COMMENT_ID:
    print("\nCould not get a real comment ID. Stopping.")
    exit(1)

print(f"\nReal comment_id = {REAL_COMMENT_ID}")
print()

# ── STEP 2: Simulate webhook with REAL comment_id ─────────────────────────────
print("=== STEP 2: Delivering webhook with real comment_id ===")
payload = {
    'object': 'instagram',
    'entry': [{
        'id': IG_ID,
        'time': int(time.time()),
        'changes': [{
            'field': 'comments',
            'value': {
                'id': REAL_COMMENT_ID,
                'from': {
                    'id': RACONZ_ID,
                    'username': 'the_raconz',
                },
                'media': {
                    'id': POST_ID,
                    'media_product_type': 'FEED'
                },
                'text': 'test1',
                'timestamp': int(time.time()),
            }
        }]
    }]
}

body = json.dumps(payload).encode('utf-8')
secret = settings.FACEBOOK_APP_SECRET
sig = 'sha256=' + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

r = requests.post(
    'http://127.0.0.1:8000/api/webhooks/instagram/',
    data=body,
    headers={'Content-Type': 'application/json', 'X-Hub-Signature-256': sig},
    timeout=10,
)
print(f"Webhook response: {r.status_code} {r.text}")
print()

# ── STEP 3: Wait and check trigger status ────────────────────────────────────
print("=== STEP 3: Waiting for Celery to process trigger ===")
from django.utils import timezone
import datetime
since = timezone.now() - datetime.timedelta(seconds=10)

for i in range(10):
    time.sleep(2)
    trigger = AutomationTrigger.objects.filter(
        comment_id=REAL_COMMENT_ID
    ).first()
    if not trigger:
        trigger = AutomationTrigger.objects.filter(
            instagram_user_id=RACONZ_ID,
            created_at__gte=since
        ).order_by('-created_at').first()
    
    if trigger:
        print(f"  [{i*2}s] Trigger status: {trigger.status}")
        if trigger.error_message:
            print(f"  Error: {trigger.error_message[:250]}")
        if trigger.status in ('sent', 'failed', 'skipped'):
            break
    else:
        print(f"  [{i*2}s] No trigger yet...")

# ── STEP 4: Clean up — delete the test comment ───────────────────────────────
print()
print("=== STEP 4: Deleting test comment ===")
del_resp = requests.delete(
    f'https://graph.instagram.com/v25.0/{REAL_COMMENT_ID}',
    headers={'Authorization': f'Bearer {TOKEN}'}
)
print(f"Delete comment: {del_resp.status_code} {del_resp.text}")
