import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from automations.models import AutomationTrigger
from django.utils import timezone
from datetime import timedelta

recent = AutomationTrigger.objects.filter(created_at__gte=timezone.now() - timedelta(hours=3)).order_by('-created_at')[:10]
print(f'Total recent triggers: {recent.count()}')
for t in recent:
    print(f'[{t.created_at.strftime("%Y-%m-%d %H:%M:%S")} UTC] id={t.id} user=@{t.instagram_username} status={t.status} comment_id={t.comment_id}')
    if t.error_message:
        print(f'   Error: {t.error_message}')
