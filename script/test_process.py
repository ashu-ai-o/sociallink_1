"""
Diagnostic script for automation trigger pipeline.
Checks: accounts, automations, recent triggers, and webhook receipt.
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import InstagramAccount
from automations.models import Automation, AutomationTrigger

print("=" * 60)
print("INSTAGRAM ACCOUNTS")
print("=" * 60)
for a in InstagramAccount.objects.all():
    print(f"  username:          @{a.username}")
    print(f"  instagram_user_id: {a.instagram_user_id}")
    print(f"  platform_id:       {a.platform_id}")
    print(f"  connection_method: {a.connection_method}")
    print(f"  is_active:         {a.is_active}")
    print()

print("=" * 60)
print("AUTOMATIONS")
print("=" * 60)
for aut in Automation.objects.all():
    account = aut.instagram_account
    print(f"  [{aut.id}] {aut.name}")
    print(f"    is_active:         {aut.is_active}")
    print(f"    trigger_type:      {aut.trigger_type}")
    print(f"    trigger_keywords:  {aut.trigger_keywords}")
    print(f"    trigger_match_type:{aut.trigger_match_type}")
    print(f"    target_posts:      {aut.target_posts}")
    print(f"    instagram_account: {account.username} ({account.instagram_user_id})")
    print()

print("=" * 60)
print("RECENT TRIGGERS (last 10)")
print("=" * 60)
recent = AutomationTrigger.objects.order_by('-created_at')[:10]
if not recent:
    print("  NO TRIGGERS FOUND - webhook is not being received or no matching automation")
for t in recent:
    print(f"  [{t.id}] status={t.status}")
    print(f"    automation: {t.automation.name}")
    print(f"    from: @{t.instagram_username}")
    print(f"    comment: {repr(t.comment_text)}")
    print(f"    post_id: {t.post_id}")
    print(f"    created: {t.created_at}")
    if t.error_message:
        print(f"    error: {t.error_message}")
    print()
