import os
import django
import json
import requests
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import InstagramAccount
from automations.models import Automation

def test_real_comment(comment_id="real_comment_id_here", user_id="26159303547039775"):
    # 1. Gather real details
    acc = InstagramAccount.objects.first()
    if not acc:
        print("ERROR: No Instagram account found.")
        return

    # 2. Get the active automation to find the target post
    automation = Automation.objects.filter(is_active=True, trigger_type='comment').first()
    if not automation:
        print("ERROR: No active comment automation found.")
        return
        
    target_post_id = automation.target_posts[0] if automation.target_posts else "18148423327459502"
    trigger_keyword = "link" # typical trigger keyword
    
    print(f"=================================================")
    print(f"Testing Real Flow with:")
    print(f"Account IG ID  : {acc.platform_id or acc.instagram_user_id}")
    print(f"Target Post ID : {target_post_id}")
    print(f"Commenter ID   : {user_id}")
    print(f"Comment ID     : {comment_id}")
    print(f"Keyword test   : '{trigger_keyword}'")
    print(f"=================================================")

    # 3. Simulate EXACT Webhook Payload matching Meta format
    url = "http://localhost:8000/api/webhooks/instagram/"
    webhook_payload = {
        "object": "instagram",
        "entry": [{
            "id": acc.platform_id or acc.instagram_user_id,
            "time": 1234567890,
            "changes": [{
                "field": "comments",
                "value": {
                    "id": comment_id,
                    "media_id": target_post_id,
                    "text": trigger_keyword,
                    "from": {
                        "id": user_id,
                        "username": "tester_username"
                    }
                }
            }]
        }]
    }

    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": "sha256=any"  # DEBUG bypass allows 'any'
    }

    print("\nSending POST request to running Django server...")
    try:
        resp = requests.post(url, json=webhook_payload, headers=headers, timeout=10)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")
    except Exception as e:
        print(f"ERROR: Could not connect to localhost:8000. Is the server running? Details: {e}")
        return

    print("\n=== Checking Database for newly created Trigger ===")
    from automations.models import AutomationTrigger
    from time import sleep
    
    # Wait a tiny bit for Celery
    sleep(1.5)
    
    # Print out latest triggers excluding the safe 'test_' bypasses
    for t in AutomationTrigger.objects.exclude(comment_id__startswith='test').order_by('-created_at')[:3]:
        print(f"  {t.created_at.strftime('%H:%M:%S')} | ID: {t.id}")
        print(f"  Status   : {t.status}")
        print(f"  Reply    : {'Sent' if t.comment_reply_sent else 'Failed/Skipped'}")
        if t.error_message:
            print(f"  Error    : {t.error_message}")
        print("  --")

if __name__ == "__main__":
    c_id = "real_comment_id_here"
    u_id = "26159303547039775"
    
    if len(sys.argv) > 1:
         c_id = sys.argv[1]
    if len(sys.argv) > 2:
         u_id = sys.argv[2]
         
    test_real_comment(c_id, u_id)
