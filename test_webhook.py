import os
import requests
import json
import hmac
import hashlib
from dotenv import load_dotenv

load_dotenv()

secret = os.getenv('INSTAGRAM_CLIENT_SECRET', '')
print(f"Using Secret: {secret[:5]}...")

payload = {
    "object": "instagram",
    "entry": [
        {
            "id": "123456789",
            "time": 1612345678,
            "messaging": [
                {
                    "sender": {"id": "123"},
                    "recipient": {"id": "456"},
                    "timestamp": 1612345678,
                    "message": {
                        "mid": "msg_123",
                        "text": "test webhook"
                    }
                }
            ]
        }
    ]
}

payload_bytes = json.dumps(payload).encode('utf-8')
signature = hmac.new(secret.encode('utf-8'), payload_bytes, hashlib.sha256).hexdigest()

print(f"Signature: sha256={signature}")

headers = {
    'Content-Type': 'application/json',
    'X-Hub-Signature-256': f'sha256={signature}'
}

try:
    r = requests.post('http://localhost:8000/api/webhooks/instagram/', data=payload_bytes, headers=headers)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")
except Exception as e:
    print(f"Error: {e}")
