"""
Analytics Celery Tasks
Background jobs for aggregating and processing analytics data
"""

from celery import shared_task
from django.utils import timezone
from django.db.models import Sum, Avg, Count
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def aggregate_daily_stats():
    """
    Aggregate daily statistics for all users
    Runs once per day at midnight
    """
    from accounts.models import User
    from automations.models import Automation, AutomationTrigger
    from .models import DailyStats
    
    yesterday = timezone.now().date() - timedelta(days=1)
    
    logger.info(f"Aggregating daily stats for {yesterday}")
    
    users = User.objects.all()
    stats_created = 0
    
    for user in users:
        # Get user's automations
        automations = Automation.objects.filter(
            instagram_account__user=user
        )
        
        # Get yesterday's triggers
        triggers = AutomationTrigger.objects.filter(
            automation__instagram_account__user=user,
            created_at__date=yesterday
        )
        
        # Calculate stats
        total_triggers = triggers.count()
        successful_triggers = triggers.filter(status='sent').count()
        failed_triggers = triggers.filter(status='failed').count()
        skipped_triggers = triggers.filter(status='skipped').count()
        ai_enhanced = triggers.filter(was_ai_enhanced=True).count()
        
        success_rate = (successful_triggers / total_triggers * 100) if total_triggers > 0 else 0
        ai_rate = (ai_enhanced / total_triggers * 100) if total_triggers > 0 else 0
        
        # Create or update daily stats
        daily_stat, created = DailyStats.objects.update_or_create(
            user=user,
            date=yesterday,
            defaults={
                'total_automations': automations.count(),
                'active_automations': automations.filter(is_active=True).count(),
                'total_triggers': total_triggers,
                'successful_triggers': successful_triggers,
                'failed_triggers': failed_triggers,
                'skipped_triggers': skipped_triggers,
                'total_dms_sent': successful_triggers,
                'ai_enhanced_dms': ai_enhanced,
                'success_rate': success_rate,
                'ai_enhancement_rate': ai_rate,
            }
        )
        
        if created:
            stats_created += 1
    
    logger.info(f"✅ Created {stats_created} daily stats for {yesterday}")
    return f"Processed {users.count()} users, created {stats_created} stats"


@shared_task
def aggregate_automation_performance():
    """
    Aggregate performance metrics for each automation
    Runs daily
    """
    from automations.models import Automation, AutomationTrigger
    from .models import AutomationPerformance
    
    yesterday = timezone.now().date() - timedelta(days=1)
    
    logger.info(f"Aggregating automation performance for {yesterday}")
    
    automations = Automation.objects.all()
    performance_created = 0
    
    for automation in automations:
        # Get yesterday's triggers for this automation
        triggers = AutomationTrigger.objects.filter(
            automation=automation,
            created_at__date=yesterday
        )
        
        triggers_count = triggers.count()
        if triggers_count == 0:
            continue
        
        successful = triggers.filter(status='sent').count()
        failed = triggers.filter(status='failed').count()
        skipped = triggers.filter(status='skipped').count()
        ai_enhanced = triggers.filter(was_ai_enhanced=True).count()
        
        success_rate = (successful / triggers_count * 100) if triggers_count > 0 else 0
        ai_rate = (ai_enhanced / triggers_count * 100) if triggers_count > 0 else 0
        
        # Create or update performance record
        performance, created = AutomationPerformance.objects.update_or_create(
            automation=automation,
            date=yesterday,
            defaults={
                'triggers_count': triggers_count,
                'successful_count': successful,
                'failed_count': failed,
                'skipped_count': skipped,
                'success_rate': success_rate,
                'ai_enhanced_count': ai_enhanced,
                'ai_enhancement_rate': ai_rate,
            }
        )
        
        if created:
            performance_created += 1
    
    logger.info(f"✅ Created {performance_created} performance records for {yesterday}")
    return f"Processed {automations.count()} automations, created {performance_created} records"


@shared_task
def aggregate_ai_metrics():
    """
    Aggregate AI provider metrics
    Runs daily
    """
    from accounts.models import User
    from automations.models import AutomationTrigger
    from .models import AIProviderMetrics
    
    yesterday = timezone.now().date() - timedelta(days=1)
    
    logger.info(f"Aggregating AI metrics for {yesterday}")
    
    users = User.objects.all()
    metrics_created = 0
    
    for user in users:
        # Get AI-enhanced triggers from yesterday
        triggers = AutomationTrigger.objects.filter(
            automation__instagram_account__user=user,
            created_at__date=yesterday,
            was_ai_enhanced=True
        )
        
        if triggers.count() == 0:
            continue
        
        # Group by AI model used (stored in ai_modifications field)
        model_stats = {}
        
        for trigger in triggers:
            if trigger.ai_modifications:
                # Parse model info from ai_modifications
                # Format: "Claude 3.5 Sonnet via OpenRouter"
                model = trigger.ai_modifications.split(' via ')[0] if ' via ' in trigger.ai_modifications else 'Unknown'
                
                if model not in model_stats:
                    model_stats[model] = {
                        'total': 0,
                        'successful': 0,
                        'failed': 0
                    }
                
                model_stats[model]['total'] += 1
                if trigger.status == 'sent':
                    model_stats[model]['successful'] += 1
                else:
                    model_stats[model]['failed'] += 1
        
        # Create metrics for each model
        for model, stats in model_stats.items():
            # Estimate cost based on model
            cost_per_request = 0.001  # Default $0.001 per request
            if 'Claude 3.5 Sonnet' in model:
                cost_per_request = 0.003
            elif 'Claude 3 Haiku' in model:
                cost_per_request = 0.00025
            elif 'GPT-4' in model:
                cost_per_request = 0.01
            elif 'GPT-3.5' in model:
                cost_per_request = 0.0005
            
            estimated_cost = stats['total'] * cost_per_request
            
            metric, created = AIProviderMetrics.objects.update_or_create(
                user=user,
                date=yesterday,
                model_used=model,
                defaults={
                    'provider': 'openrouter',
                    'total_requests': stats['total'],
                    'successful_requests': stats['successful'],
                    'failed_requests': stats['failed'],
                    'estimated_cost': estimated_cost,
                }
            )
            
            if created:
                metrics_created += 1
    
    logger.info(f"✅ Created {metrics_created} AI metrics for {yesterday}")
    return f"Processed {users.count()} users, created {metrics_created} metrics"


@shared_task
def aggregate_contact_engagement():
    """
    Aggregate contact engagement metrics
    Runs daily
    """
    from automations.models import Contact, AutomationTrigger
    from .models import ContactEngagement
    
    yesterday = timezone.now().date() - timedelta(days=1)
    
    logger.info(f"Aggregating contact engagement for {yesterday}")
    
    contacts = Contact.objects.all()
    engagement_created = 0
    
    for contact in contacts:
        # Get triggers for this contact from yesterday
        triggers = AutomationTrigger.objects.filter(
            instagram_user_id=contact.instagram_user_id,
            created_at__date=yesterday
        )
        
        dms_count = triggers.filter(status='sent').count()
        if dms_count == 0:
            continue
        
        ai_enhanced = triggers.filter(was_ai_enhanced=True).count()
        
        # Create engagement record
        engagement, created = ContactEngagement.objects.update_or_create(
            contact=contact,
            date=yesterday,
            defaults={
                'dms_received': dms_count,
                'ai_enhanced_dms': ai_enhanced,
            }
        )
        
        if created:
            engagement_created += 1
    
    logger.info(f"✅ Created {engagement_created} engagement records for {yesterday}")
    return f"Processed {contacts.count()} contacts, created {engagement_created} records"


@shared_task
def log_system_event(user_id, event_type, description='', metadata=None, severity='info', automation_id=None, instagram_account_id=None):
    """
    Log a system event
    Called from other parts of the application
    
    Usage:
    from analytics.tasks import log_system_event
    log_system_event.delay(
        user_id=user.id,
        event_type='automation_created',
        description='New automation created',
        metadata={'automation_name': 'My Automation'}
    )
    """
    from accounts.models import User
    from .models import SystemEvent
    
    try:
        user = User.objects.get(id=user_id) if user_id else None
        
        event = SystemEvent.objects.create(
            user=user,
            event_type=event_type,
            description=description,
            metadata=metadata or {},
            severity=severity,
            automation_id=automation_id,
            instagram_account_id=instagram_account_id
        )
        
        logger.info(f"✅ Logged system event: {event_type} for user {user_id}")
        return str(event.id)
    except Exception as e:
        logger.error(f"❌ Failed to log system event: {str(e)}")
        return None


@shared_task
def cleanup_old_analytics():
    """
    Clean up old analytics data (older than 1 year)
    Runs weekly
    """
    from .models import DailyStats, AutomationPerformance, AIProviderMetrics, ContactEngagement, WebhookLog
    
    cutoff_date = timezone.now().date() - timedelta(days=365)
    
    logger.info(f"Cleaning up analytics data older than {cutoff_date}")
    
    # Delete old records
    daily_stats_deleted = DailyStats.objects.filter(date__lt=cutoff_date).delete()[0]
    performance_deleted = AutomationPerformance.objects.filter(date__lt=cutoff_date).delete()[0]
    ai_metrics_deleted = AIProviderMetrics.objects.filter(date__lt=cutoff_date).delete()[0]
    engagement_deleted = ContactEngagement.objects.filter(date__lt=cutoff_date).delete()[0]
    webhook_deleted = WebhookLog.objects.filter(created_at__lt=timezone.now() - timedelta(days=90)).delete()[0]
    
    total_deleted = daily_stats_deleted + performance_deleted + ai_metrics_deleted + engagement_deleted + webhook_deleted
    
    logger.info(f"✅ Cleaned up {total_deleted} old analytics records")
    return {
        'total_deleted': total_deleted,
        'daily_stats': daily_stats_deleted,
        'performance': performance_deleted,
        'ai_metrics': ai_metrics_deleted,
        'engagement': engagement_deleted,
        'webhooks': webhook_deleted
    }


@shared_task
def generate_weekly_report(user_id):
    """
    Generate weekly analytics report for a user
    Can be triggered on-demand or scheduled
    """
    from accounts.models import User
    from .models import DailyStats
    
    try:
        user = User.objects.get(id=user_id)
        
        # Get last 7 days
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=7)
        
        stats = DailyStats.objects.filter(
            user=user,
            date__gte=start_date,
            date__lte=end_date
        )
        
        # Calculate weekly totals
        total_triggers = sum(s.total_triggers for s in stats)
        total_dms = sum(s.total_dms_sent for s in stats)
        avg_success_rate = sum(s.success_rate for s in stats) / len(stats) if stats else 0
        avg_ai_rate = sum(s.ai_enhancement_rate for s in stats) / len(stats) if stats else 0
        
        report = {
            'user_id': str(user.id),
            'user_email': user.email,
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'total_triggers': total_triggers,
            'total_dms_sent': total_dms,
            'avg_success_rate': round(avg_success_rate, 2),
            'avg_ai_enhancement_rate': round(avg_ai_rate, 2),
            'daily_breakdown': [
                {
                    'date': s.date.isoformat(),
                    'triggers': s.total_triggers,
                    'dms_sent': s.total_dms_sent,
                    'success_rate': s.success_rate
                }
                for s in stats
            ]
        }
        
        logger.info(f"✅ Generated weekly report for user {user.email}")
        
        # TODO: Send email with report
        # send_weekly_report_email.delay(user.email, report)
        
        return report
    except User.DoesNotExist:
        logger.error(f"❌ User {user_id} not found")
        return None
    except Exception as e:
        logger.error(f"❌ Failed to generate weekly report: {str(e)}")
        return None


@shared_task
def calculate_automation_roi(automation_id):
    """
    Calculate ROI for a specific automation
    """
    from automations.models import Automation
    from .models import AutomationPerformance
    
    try:
        automation = Automation.objects.get(id=automation_id)
        
        # Get last 30 days performance
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        performance = AutomationPerformance.objects.filter(
            automation=automation,
            date__gte=start_date,
            date__lte=end_date
        )
        
        total_triggers = sum(p.triggers_count for p in performance)
        total_successful = sum(p.successful_count for p in performance)
        total_clicks = sum(p.click_count for p in performance)
        
        # Calculate estimated value (customize based on business)
        value_per_click = 5.00  # $5 per click (example)
        estimated_revenue = total_clicks * value_per_click
        
        # Calculate cost (AI + time)
        ai_cost = total_successful * 0.003  # Average AI cost per message
        
        roi = {
            'automation_id': str(automation.id),
            'automation_name': automation.name,
            'period_days': 30,
            'total_triggers': total_triggers,
            'total_successful': total_successful,
            'total_clicks': total_clicks,
            'estimated_revenue': estimated_revenue,
            'estimated_cost': ai_cost,
            'roi': ((estimated_revenue - ai_cost) / ai_cost * 100) if ai_cost > 0 else 0
        }
        
        logger.info(f"✅ Calculated ROI for automation {automation.name}")
        return roi
    except Automation.DoesNotExist:
        logger.error(f"❌ Automation {automation_id} not found")
        return None
    except Exception as e:
        logger.error(f"❌ Failed to calculate ROI: {str(e)}")
        return None


# Schedule tasks in celery beat
"""
Add to core/celery.py:

from celery.schedules import crontab

app.conf.beat_schedule = {
    'aggregate-daily-stats': {
        'task': 'analytics.tasks.aggregate_daily_stats',
        'schedule': crontab(hour=0, minute=5),  # 00:05 AM daily
    },
    'aggregate-automation-performance': {
        'task': 'analytics.tasks.aggregate_automation_performance',
        'schedule': crontab(hour=0, minute=10),  # 00:10 AM daily
    },
    'aggregate-ai-metrics': {
        'task': 'analytics.tasks.aggregate_ai_metrics',
        'schedule': crontab(hour=0, minute=15),  # 00:15 AM daily
    },
    'aggregate-contact-engagement': {
        'task': 'analytics.tasks.aggregate_contact_engagement',
        'schedule': crontab(hour=0, minute=20),  # 00:20 AM daily
    },
    'cleanup-old-analytics': {
        'task': 'analytics.tasks.cleanup_old_analytics',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # 2 AM every Sunday
    },
}
"""