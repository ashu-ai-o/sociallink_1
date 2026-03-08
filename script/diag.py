import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from automations.models import Automation, AutomationTrigger
from accounts.models import InstagramAccount
from django.conf import settings

print("=== BACKEND_URL ===")
print(f"  {settings.BACKEND_URL}")

print()
print("=== WEBHOOK VERIFY TOKEN ===")
print(f"  {settings.INSTAGRAM_WEBHOOK_VERIFY_TOKEN}")

print()
print("=== INSTAGRAM ACCOUNTS ===")
for acc in InstagramAccount.objects.all():
    print(f"  ID={acc.id} | IG_USER_ID={acc.instagram_user_id} | @{acc.username} | active={acc.is_active} | method={acc.connection_method}")

print()
print("=== AUTOMATIONS ===")
for a in Automation.objects.all():
    print(f"  [{'ACTIVE' if a.is_active else 'INACTIVE'}] '{a.name}'")
    print(f"    trigger={a.trigger_type} | match={a.trigger_match_type} | keywords={a.trigger_keywords}")
    print(f"    target_posts={a.target_posts}")
    print(f"    account_ig_user_id={a.instagram_account.instagram_user_id if a.instagram_account_id else 'NONE'}")

print()
print("=== RECENT TRIGGERS (last 20) ===")
for t in AutomationTrigger.objects.order_by('-created_at')[:20]:
    line = f"  {t.created_at.isoformat()} | status={t.status:10} | @{t.instagram_username:15} | comment='{t.comment_text[:30]}'"
    line += f" | reply_sent={t.comment_reply_sent} | err='{t.error_message}'"
    print(line)

if not AutomationTrigger.objects.exists():
    print("  [NONE] No triggers recorded at all - webhook is NOT reaching the server")
