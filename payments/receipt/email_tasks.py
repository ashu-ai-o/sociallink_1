"""
Celery Tasks for Email Notifications
Handles async email sending with retry mechanism
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from .email_service import EmailService

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=900,  # 15 minutes max
    retry_jitter=True
)
def send_payment_receipt_email(self, payment_id: str):
    """
    Send payment receipt email asynchronously with retry mechanism
    
    Args:
        payment_id: UUID string of the payment
        
    Retry Strategy:
        - Attempt 1: Immediate
        - Attempt 2: After 5 minutes
        - Attempt 3: After 10 minutes (exponential backoff)
        - Attempt 4: After 15 minutes (max backoff)
        - Final failure: Log critical error
    """
    try:
        logger.info(f"Sending payment receipt for payment {payment_id}")
        
        result = EmailService.send_payment_receipt(payment_id)
        
        if result.get('success'):
            if result.get('skipped'):
                logger.info(f"⏭️ Receipt email skipped for payment {payment_id}: {result.get('message')}")
            else:
                logger.info(f"Receipt email sent successfully for payment {payment_id}")
            return result
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"Receipt email failed for payment {payment_id}: {error_msg}")
            raise Exception(error_msg)
            
    except Exception as exc:
        logger.error(
            f"❌ Attempt {self.request.retries + 1}/3 failed for payment {payment_id}: {str(exc)}"
        )
        
        # On final failure, log to error tracking
        if self.request.retries >= 2:
            logger.critical(
                f"🚨 CRITICAL: All retry attempts exhausted for payment receipt {payment_id}. "
                f"Manual intervention required. Error: {str(exc)}"
            )
            
            # Store failed email for admin review
            try:
                from payments.models import EmailLog
                EmailLog.objects.create(
                    payment_id=payment_id,
                    email_type='payment_receipt',
                    status='failed_final',
                    error_message=f"All retries exhausted: {str(exc)}",
                    metadata={'retries': self.request.retries + 1}
                )
            except Exception:
                pass
        
        # Retry the task
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=900,  # 15 minutes max
    retry_jitter=True
)
def send_payment_failure_email(self, payment_id: str):
    """
    Send payment failure notification email asynchronously with retry mechanism
    
    Args:
        payment_id: UUID string of the failed payment
        
    Retry Strategy:
        - Attempt 1: Immediate
        - Attempt 2: After 5 minutes
        - Attempt 3: After 10 minutes (exponential backoff)
        - Attempt 4: After 15 minutes (max backoff)
        - Final failure: Log critical error
    """
    try:
        logger.info(f"Sending payment failure notification for payment {payment_id}")
        
        result = EmailService.send_payment_failure(payment_id)
        
        if result.get('success'):
            if result.get('skipped'):
                logger.info(f"⏭️ Failure email skipped for payment {payment_id}: {result.get('message')}")
            else:
                logger.info(f"Failure email sent successfully for payment {payment_id}")
            return result
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"Failure email failed for payment {payment_id}: {error_msg}")
            raise Exception(error_msg)
            
    except Exception as exc:
        logger.error(
            f"❌ Attempt {self.request.retries + 1}/3 failed for payment failure {payment_id}: {str(exc)}"
        )
        
        # On final failure, log to error tracking
        if self.request.retries >= 2:
            logger.critical(
                f"🚨 CRITICAL: All retry attempts exhausted for payment failure email {payment_id}. "
                f"Manual intervention required. Error: {str(exc)}"
            )
            
            # Store failed email for admin review
            try:
                from payments.models import EmailLog
                EmailLog.objects.create(
                    payment_id=payment_id,
                    email_type='payment_failure',
                    status='failed_final',
                    error_message=f"All retries exhausted: {str(exc)}",
                    metadata={'retries': self.request.retries + 1}
                )
            except Exception:
                pass
        
        # Retry the task
        raise self.retry(exc=exc)


@shared_task
def cleanup_old_email_logs():
    """
    Cleanup email logs older than 90 days
    Runs daily via Celery Beat
    """
    try:
        from payments.models import EmailLog
        
        cutoff_date = timezone.now() - timedelta(days=90)
        deleted_count, _ = EmailLog.objects.filter(
            created_at__lt=cutoff_date
        ).delete()
        
        logger.info(f"Cleaned up {deleted_count} old email logs")
        return f"Deleted {deleted_count} email logs"
        
    except Exception as e:
        logger.error(f"Error cleaning up email logs: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def send_email_analytics_report():
    """
    Send weekly email analytics report to admin
    Runs weekly via Celery Beat
    """
    try:
        from payments.models import EmailLog
        from django.core.mail import send_mail
        from django.conf import settings
        from django.db.models import Count
        
        # Get last 7 days stats
        week_ago = timezone.now() - timedelta(days=7)
        
        stats = EmailLog.objects.filter(
            created_at__gte=week_ago
        ).values('email_type', 'status').annotate(
            count=Count('id')
        )
        
        # Format report
        report = "Email Analytics Report (Last 7 Days)\n\n"
        for stat in stats:
            report += f"{stat['email_type']}.{stat['status']}: {stat['count']}\n"
        
        # Send to admin
        send_mail(
            subject='Weekly Email Analytics Report',
            message=report,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMINS[0][1]] if settings.ADMINS else [],
            fail_silently=True
        )
        
        logger.info("Email analytics report sent")
        return "Report sent"
        
    except Exception as e:
        logger.error(f"Error sending email report: {str(e)}")
        return f"Error: {str(e)}"