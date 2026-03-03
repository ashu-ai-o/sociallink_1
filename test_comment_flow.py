"""
Comment Flow Diagnostic
=======================
Checks every layer of the comment → comment reply + DM flow:
  1. Celery / Redis reachability
  2. Automation configuration
  3. Recent trigger statuses
  4. End-to-end webhook simulation + trigger result

Run: python test_comment_flow.py
"""

import os, django, json, time
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings

print("=" * 60)
print("COMMENT FLOW DIAGNOSTIC")
print("=" * 60)

# ── 1. Check Redis / Celery broker ───────────────────────────────
print("\n[1] Checking Celery broker (Redis)...")
try:
    import redis
    broker_url = getattr(settings, 'CELERY_BROKER_URL', None) or getattr(settings, 'BROKER_URL', 'redis://localhost:6379/0')
    r = redis.from_url(broker_url)
    r.ping()
    print(f"  ✅ Redis reachable at: {broker_url}")
except Exception as e:
    print(f"  ❌ Redis NOT reachable: {e}")
    print("  → Celery workers cannot run without Redis. Triggers will stay 'pending' forever.")
    print("  → Start Redis: redis-server  OR  docker run -p 6379:6379 redis")

# ── 2. Check Celery active workers ───────────────────────────────
print("\n[2] Checking Celery workers...")
try:
    from core.celery import app as celery_app
    inspect = celery_app.control.inspect(timeout=3)
    active = inspect.active()
    if active:
        worker_names = list(active.keys())
        print(f"  ✅ Active workers: {worker_names}")
    else:
        print("  ❌ No active Celery workers found.")
        print("  → Start a worker: celery -A core worker -l info")
except Exception as e:
    print(f"  ⚠️  Could not inspect workers: {e}")

# ── 3. Automation configuration ───────────────────────────────────
print("\n[3] Automation configuration...")
from accounts.models import InstagramAccount
from automations.models import Automation, AutomationTrigger

accounts = InstagramAccount.objects.filter(is_active=True)
for account in accounts:
    print(f"\n  Account: @{account.username}  ({account.connection_method})")
    print(f"    instagram_user_id : {account.instagram_user_id}")
    print(f"    page_id           : {account.page_id}")
    token_preview = account.access_token[:20] + '...' if account.access_token else 'MISSING'
    print(f"    access_token      : {token_preview}")
    if hasattr(account, 'token_expires_at') and account.token_expires_at:
        from django.utils import timezone
        expired = account.token_expires_at < timezone.now()
        status = '❌ EXPIRED' if expired else '✅ valid'
        print(f"    token_expires_at  : {account.token_expires_at}  [{status}]")

    automations = Automation.objects.filter(instagram_account=account, is_active=True)
    print(f"\n    Active automations: {automations.count()}")
    for a in automations:
        print(f"      • [{a.trigger_type}] \"{a.name}\"")
        print(f"          keywords    : {a.trigger_keywords}  (match: {a.trigger_match_type})")
        print(f"          target_posts: {a.target_posts or 'ALL POSTS'}")
        print(f"          comment_reply_enabled : {a.enable_comment_reply}")
        print(f"          comment_reply_message : '{a.comment_reply_message}'")
        dm_preview = (a.DmMessage[:60] + '...') if len(a.DmMessage) > 60 else a.DmMessage
        print(f"          DmMessage   : '{dm_preview}'")
        print(f"          total_triggers: {a.total_triggers}  |  total_dms_sent: {a.total_dms_sent}")

# ── 4. Recent trigger statuses ────────────────────────────────────
print("\n[4] Most recent triggers (last 10)...")
triggers = AutomationTrigger.objects.select_related('automation').order_by('-created_at')[:10]
if not triggers:
    print("  (no triggers in database yet)")
else:
    for t in triggers:
        err = f"  err='{t.error_message[:60]}'" if t.error_message else ''
        print(f"  {t.created_at.strftime('%Y-%m-%d %H:%M:%S')} | "
              f"status={t.status:<12} | "
              f"@{t.instagram_username or t.instagram_user_id} | "
              f"'{t.comment_text[:30]}'"
              f"{err}")

# ── 5. End-to-end webhook + trigger result test ───────────────────
print("\n[5] Simulating comment webhook...")

import requests

account = InstagramAccount.objects.filter(is_active=True).first()
if not account:
    print("  ❌ No active account — skipping webhook test")
else:
    # Use entry id appropriate for connection method
    entry_id = account.page_id if (account.connection_method == 'facebook_graph' and account.page_id) else account.instagram_user_id

    # Try to match an existing automation's target post and keyword
    automation = Automation.objects.filter(
        instagram_account=account,
        is_active=True,
        trigger_type='comment'
    ).first()

    if not automation:
        print("  ❌ No active comment automation found for this account")
    else:
        # Choose test post id and keyword
        post_id = automation.target_posts[0] if automation.target_posts else "18148423327459502"
        if automation.trigger_match_type == 'any':
            keyword = "test comment"
        elif automation.trigger_keywords:
            keyword = automation.trigger_keywords[0]
        else:
            keyword = "link please"

        print(f"  Account    : @{account.username}")
        print(f"  Entry id   : {entry_id}")
        print(f"  Automation : {automation.name}")
        print(f"  Post id    : {post_id}")
        print(f"  Keyword    : '{keyword}'")

        before_count = AutomationTrigger.objects.filter(automation=automation).count()

        payload = {
            "object": "instagram",
            "entry": [{
                "id": entry_id,
                "time": 1234567890,
                "changes": [{
                    "field": "comments",
                    "value": {
                        "id": f"test_comment_{int(time.time())}",
                        "media_id": post_id,
                        "text": keyword,
                        "from": {
                            "id": "111222333444",
                            "username": "test_commenter"
                        }
                    }
                }]
            }]
        }

        headers = {
            "Content-Type": "application/json",
            "X-Hub-Signature-256": "sha256=any"
        }

        try:
            resp = requests.post(
                "http://localhost:8000/api/webhooks/instagram/",
                json=payload,
                headers=headers,
                timeout=10
            )
            print(f"\n  Webhook response: {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"\n  ❌ Could not reach server: {e}")
            print("  → Make sure Django server is running: python manage.py runserver")

        # Wait a moment and check for new trigger
        time.sleep(1)
        after_count = AutomationTrigger.objects.filter(automation=automation).count()
        new_triggers = after_count - before_count

        if new_triggers > 0:
            print(f"\n  ✅ {new_triggers} trigger(s) created in DB")
            latest = AutomationTrigger.objects.filter(automation=automation).order_by('-created_at').first()
            print(f"     status       : {latest.status}")
            print(f"     error        : {latest.error_message or '(none)'}")
            if latest.status == 'pending':
                print("  ⚠️  Trigger is still 'pending' — Celery worker is NOT processing it.")
                print("     Start worker: celery -A core worker -l info")
            elif latest.status == 'sent':
                print("  ✅ DM was sent successfully!")
            elif latest.status == 'failed':
                print(f"  ❌ Processing failed: {latest.error_message}")
            elif latest.status == 'skipped':
                print(f"  ⏭️  Skipped (24-hour rate limit for this user): {latest.error_message}")
        else:
            print("\n  ❌ No trigger created — webhook did not match any automation")
            print("     Check: does the keyword match the automation trigger keywords?")
            print("     Check: does the post_id match the automation target_posts?")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
