import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'linkplease.settings')

app = Celery('linkplease')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Concurrency settings for 10K+ users
app.conf.update(
    worker_prefetch_multiplier=1,  # Prevent worker hogging tasks
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
    task_acks_late=True,  # Acknowledge after completion
    task_reject_on_worker_lost=True,
    broker_pool_limit=None,  # No limit on broker connections
)

# Beat schedule - runs in background
app.conf.beat_schedule = {
    'check-comments-every-30s': {
        'task': 'automations.tasks.check_comments_bulk_async',
        'schedule': 30.0,  # Every 30 seconds
    },
}
