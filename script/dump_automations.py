import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from automations.models import Automation

for a in Automation.objects.all():
    print(f"Automation: {a.name}")
    print(f"  Trigger: {a.trigger_type}")
    print(f"  Match: {a.trigger_match_type}")
    print(f"  Keywords: {a.trigger_keywords}")
    print(f"  Target Posts (raw): {a.target_posts}")
    print(f"  Is Active: {a.is_active}")
    print(f"  Account ID: {a.instagram_account_id}")
    print(f"  Comment Reply Message: {a.comment_reply_message}")
    print(f"  Enable Comment Reply: {a.enable_comment_reply}")
    print(f"  DM Message: {a.DmMessage}")
