"""
DM Webhook Test
===============
Simulates a Meta webhook POST for an incoming DM (messaging event).
Uses DEBUG signature bypass so no HMAC key is needed.

Run:  python test_dm_webhook.py
"""

import os, django, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

import requests
from accounts.models import InstagramAccount
from automations.models import AutomationTrigger, Automation

# ── 1. Find a connected account ─────────────────────────────────────────────
try:
    account = InstagramAccount.objects.filter(is_active=True).first()
    if not account:
        print("ERROR: No active InstagramAccount found in database.")
        exit(1)
except Exception as e:
    print(f"ERROR fetching account: {e}")
    exit(1)

print(f"Testing with account: @{account.username}")
print(f"  instagram_user_id : {account.instagram_user_id}")
print(f"  page_id           : {account.page_id}")
print(f"  connection_method : {account.connection_method}")

# ── 2. Decide which ID to use as entry.id ───────────────────────────────────
# For instagram_platform → entry.id == instagram_user_id
# For facebook_graph     → entry.id == page_id
if account.connection_method == 'facebook_graph' and account.page_id:
    entry_id = account.page_id
    print(f"\n[INFO] Using page_id as entry id (facebook_graph connection)")
else:
    entry_id = account.instagram_user_id
    print(f"\n[INFO] Using instagram_user_id as entry id (instagram_platform connection)")

# ── 3. Check whether a dm_keyword automation exists ─────────────────────────
dm_automations = Automation.objects.filter(
    instagram_account=account,
    is_active=True,
    trigger_type='dm_keyword'
)
print(f"\nActive dm_keyword automations: {dm_automations.count()}")
for a in dm_automations:
    print(f"  • {a.name}  |  match={a.trigger_match_type}  |  keywords={a.trigger_keywords}")

# Choose a test message that will match
test_text = "hello"
if dm_automations.exists():
    a = dm_automations.first()
    if a.trigger_match_type == 'any':
        test_text = "any message"
    elif a.trigger_keywords:
        test_text = a.trigger_keywords[0]

print(f"\nTest DM text: '{test_text}'")

# ── 4. Build the webhook payload ─────────────────────────────────────────────
# This mirrors exactly what Meta sends for an incoming DM
payload = {
    "object": "instagram",
    "entry": [{
        "id": entry_id,
        "time": 1234567890,
        "messaging": [{
            "sender":    {"id": "999000111222"},   # fake external user
            "recipient": {"id": entry_id},
            "timestamp": 1234567890,
            "message": {
                "mid": "test_dm_mid_001",
                "text": test_text
            }
        }]
    }]
}

headers = {
    "Content-Type": "application/json",
    "X-Hub-Signature-256": "sha256=any"   # DEBUG bypass
}

# ── 5. Count triggers before ─────────────────────────────────────────────────
before_count = AutomationTrigger.objects.filter(
    automation__instagram_account=account,
    automation__trigger_type='dm_keyword'
).count()

# ── 6. Send the test webhook ─────────────────────────────────────────────────
url = "http://localhost:8000/api/webhooks/instagram/"
print(f"\nPOSTing to {url} ...")
try:
    resp = requests.post(url, json=payload, headers=headers, timeout=10)
    print(f"Status : {resp.status_code}")
    print(f"Body   : {resp.text}")
except Exception as e:
    print(f"ERROR: Could not reach server — {e}")
    print("Make sure Django dev server is running: python manage.py runserver")
    exit(1)

# ── 7. Check for new triggers ────────────────────────────────────────────────
print("\n=== DM Triggers (newest 5) ===")
after_count = AutomationTrigger.objects.filter(
    automation__instagram_account=account,
    automation__trigger_type='dm_keyword'
).count()

triggers = AutomationTrigger.objects.filter(
    automation__instagram_account=account,
    automation__trigger_type='dm_keyword'
).order_by('-created_at')[:5]

for t in triggers:
    print(f"  {t.created_at.strftime('%H:%M:%S')} | status={t.status} | user={t.instagram_user_id} | '{t.comment_text}' | err='{t.error_message[:80] if t.error_message else ''}'")

new_triggers = after_count - before_count
if new_triggers > 0:
    print(f"\n✅ SUCCESS — {new_triggers} new DM trigger(s) created")
else:
    print("\n❌ FAIL — No new DM triggers created. Check server logs for details.")
    if not dm_automations.exists():
        print("   Hint: No active dm_keyword automations found for this account.")
