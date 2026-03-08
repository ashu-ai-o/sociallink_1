"""
Simulate a webhook POST from Instagram to test the full pipeline locally.
Sends a fake comment webhook to Django and checks if a trigger is created.
"""
import os, django, json, requests as req

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import InstagramAccount
from automations.models import Automation, AutomationTrigger

account = InstagramAccount.objects.first()
automation = Automation.objects.filter(is_active=True, trigger_type='comment').first()

print("Account instagram_user_id:", account.instagram_user_id)
print("Automation:", automation.name if automation else "NONE")
print("Automation target_posts:", automation.target_posts if automation else "N/A")
print()

if not automation:
    print("ERROR: No active comment automation found!")
    exit(1)

# The post_id must be in target_posts OR target_posts must be empty
post_id = automation.target_posts[0] if automation.target_posts else "test_post_123"
print(f"Using post_id: {post_id}")

# Simulate the exact webhook payload Meta sends
payload = {
    "object": "instagram",
    "entry": [
        {
            "id": account.instagram_user_id,  # This is what Meta sends as entry.id
            "time": 1709999999,
            "changes": [
                {
                    "field": "comments",
                    "value": {
                        "media_id": post_id,
                        "id": "17858893269000001",  # fake comment_id
                        "text": "link",             # matches keyword 'link'
                        "from": {
                            "id": "9999999999",
                            "username": "test_commenter"
                        },
                        "timestamp": "2026-03-03T00:00:00+0000"
                    }
                }
            ]
        }
    ]
}

print("Sending simulated webhook to localhost:8000...")
try:
    response = req.post(
        "http://localhost:8000/api/webhooks/instagram/",
        json=payload,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": "sha256=any",  # bypass in DEBUG mode
        },
        timeout=15
    )
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")

print()
print("Checking for triggers created...")
import time; time.sleep(2)

triggers = AutomationTrigger.objects.order_by('-created_at')[:5]
if triggers:
    for t in triggers:
        print(f"  [{t.id}] status={t.status} from=@{t.instagram_username} comment={repr(t.comment_text)} post={t.post_id}")
        if t.error_message:
            print(f"         error: {t.error_message}")
else:
    print("  NO TRIGGERS CREATED - webhook processing failed")
