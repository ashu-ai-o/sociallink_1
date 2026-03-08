import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')
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
    # 'check-comments-every-30s': {
    #     'task': 'automations.tasks.check_comments_bulk_async',
    #     'schedule': 30.0,  # Every 30 seconds
    # },

    'send-weekly-reports': {
        'task': 'analytics.tasks.send_weekly_reports',
        'schedule': crontab(day_of_week=1, hour=9, minute=0),  # Monday 9am
    },

    'process-queued-triggers': {
        'task': 'automations.tasks.process_queued_triggers',
        'schedule': crontab(minute=0),  # Every hour at :00
    },
    
    # Optional: Comment polling fallback — only enable if webhooks are unavailable
    # Since webhooks are configured, this is kept disabled to avoid log spam.
    # 'check-comments-fallback': {
    #     'task': 'automations.tasks.check_comments_bulk_async',
    #     'schedule': crontab(minute='*/5'),
    # },
}
