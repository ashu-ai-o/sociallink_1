import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from automations.webhooks import process_entry

def test_process():
    payload = {
        "id": "25831541729844493",
        "time": 123,
        "changes": [
            {
                "field": "comments",
                "value": {
                    "media_id": "test_post",
                    "id": "test_comment_123",
                    "text": "link please",
                    "from": {"id": "test_fan_id", "username": "tester"}
                }
            }
        ]
    }
    
    try:
        process_entry(payload)
        print("Success! process_entry did not raise an exception.")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_process()
