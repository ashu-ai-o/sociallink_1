import os, django, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

import requests

# Simulate a webhook POST the same way Meta would send it
# Uses the DEBUG bypass signature 'any' which the webhook handler allows
url = "http://localhost:8000/api/webhooks/instagram/"

payload = {
    "entry": [{
        "id": "25831541729844493",  # wanderwithraconz IG user ID
        "time": 1234567890,
        "changes": [{
            "field": "comments",
            "value": {
                "id": "test_comment_999",
                "media_id": "18148423327459502",  # target post in automation
                "text": "send link please",
                "from": {
                    "id": "111222333",
                    "username": "testcommentor"
                }
            }
        }]
    }]
}

headers = {
    "Content-Type": "application/json",
    "X-Hub-Signature-256": "sha256=any"  # DEBUG bypass
}

print("Sending test webhook...")
try:
    resp = requests.post(url, json=payload, headers=headers, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"ERROR: {e}")

print()
print("=== Checking for new triggers ===")
from automations.models import AutomationTrigger
for t in AutomationTrigger.objects.order_by('-created_at')[:5]:
    print(f"  {t.created_at.strftime('%H:%M:%S')} | status={t.status} | @{t.instagram_username} | '{t.comment_text}' | err='{t.error_message[:80]}'")
