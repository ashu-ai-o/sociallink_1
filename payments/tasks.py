from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import UserSubscription, TokenUsage, Payment
from .razorpay_service import RazorpayService
from django.db import transaction
import logging
from django.db.models import F
from .models import Referral, UserSubscription
from django.conf import settings as django_settings
from .audit import log_payment_event
logger = logging.getLogger(__name__)



def _send_task_notification(
    user,
    email_type: str,
    subject: str,
    context: dict,
    template_name: str = None,
):
   
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags
     
    from .models import EmailLog

    try:
        # Ensure common context vars
        context.setdefault('company_name', 'dm-me')
        context.setdefault('frontend_url', django_settings.FRONTEND_URL)
        context.setdefault('support_email', 'support@dm-me.com')
        context.setdefault('user', user)

        html_message = None

        # Try the specific template first
        if template_name:
            try:
                html_message = render_to_string(template_name, context)
            except Exception:
                pass  # Template doesn't exist yet, fall through

        # Try the base template as fallback
        if not html_message:
            try:
                html_message = render_to_string('emails/base_email_minimal.html', {
                    **context,
                    'content_override': context.get('plain_message', subject),
                })
            except Exception:
                pass  # Base template also missing, use plain text only

        # Build plain text version
        plain_message = context.get('plain_message', subject)
        if html_message:
            plain_message = strip_tags(html_message)

        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        if html_message:
            email.attach_alternative(html_message, 'text/html')

        email.send(fail_silently=False)

        # Log success
        EmailLog.objects.create(
            user=user,
            email_type=email_type,
            recipient=user.email,
            subject=subject,
            status='sent',
            metadata=context.get('log_metadata', {}),
        )

        return True

    except Exception as e:
        logger.error(f"Failed to send {email_type} email to {user.email}: {e}")

        # Log failure
        try:
            EmailLog.objects.create(
                user=user,
                email_type=email_type,
                recipient=user.email,
                subject=subject,
                status='failed',
                error_message=str(e),
                metadata=context.get('log_metadata', {}),
            )
        except Exception:
            pass

        return False


def _create_in_app_notification(user, notification_type, title, message, metadata=None):
    """
    Create an in-app notification instead of sending an email.
    Used for low-priority events (downgrade warnings, low balance, plan changes).

    TODO: Replace the logger call below with your Notification model once created:
        Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            metadata=metadata or {},
            is_read=False,
        )
    """
    logger.info(
        f"IN-APP NOTIFICATION [{notification_type}] "
        f"user={user.id} ({user.username}): {title}"
    )
    # Placeholder: store in DB when Notification model exists
    return True


@shared_task
def reset_daily_token_usage():
    """
    Reset daily token usage counter for all active subscriptions
    Should run at midnight every day
    """
    active_subscriptions = UserSubscription.objects.filter(
        status__in=['active', 'trial']
    )
    
    count = 0
    for subscription in active_subscriptions:
        subscription.reset_daily_usage()
        count += 1
    
    return f"Reset daily usage for {count} subscriptions"

@shared_task
def check_auto_refill_thresholds():
    """
    Find users who opted into auto-refill and whose token balance
    has dropped below their configured threshold. Trigger a purchase
    for each one.

    Runs every 15 minutes via Celery Beat.

    Model fields used:
    - auto_refill_enabled (bool)
    - auto_refill_threshold (int, default 1000)
    - auto_refill_package (FK to TokenPackage, nullable)

    The model already has a check_and_refill() method, but it's only
    called reactively (when tokens are consumed). This task catches
    cases where consumption happened outside that code path, or where
    the reactive check was skipped due to errors.
    """

    triggered = 0
    skipped = 0
    errors = 0

    subscriptions = UserSubscription.objects.filter(
        auto_refill_enabled=True,
        auto_refill_package__isnull=False,
        status__in=['active', 'trial'],
    ).select_related('auto_refill_package', 'user')

    for sub in subscriptions:
        try:
            # Total available = plan tokens + bonus tokens
            total_available = sub.tokens_remaining + sub.bonus_tokens

            if total_available > sub.auto_refill_threshold:
                continue  # Still above threshold, skip

            # Prevent rapid re-triggering: check if we already purchased
            # for this user in the last 30 minutes
            recent_refill = Payment.objects.filter(
                user=sub.user,
                payment_type='token_purchase',
                status__in=['success', 'pending'],
                created_at__gte=timezone.now() - timedelta(minutes=30),
                metadata__auto_refill=True,
            ).exists()

            if recent_refill:
                skipped += 1
                logger.info(
                    f"Skipping auto-refill for user {sub.user.id} — "
                    f"already triggered in last 30 min"
                )
                continue

            # Trigger the purchase
            auto_purchase_tokens.delay(sub.user.id, sub.auto_refill_package.id)
            triggered += 1

            logger.info(
                f"Auto-refill triggered for user {sub.user.id}: "
                f"{total_available} tokens < threshold {sub.auto_refill_threshold}"
            )

        except Exception as e:
            errors += 1
            logger.error(f"Error checking auto-refill for subscription {sub.id}: {e}")

    logger.info(
        f"Auto-refill check complete: {triggered} triggered, "
        f"{skipped} skipped (cooldown), {errors} errors"
    )

    return {
        'triggered': triggered,
        'skipped': skipped,
        'errors': errors,
    }

@shared_task
def check_expired_subscriptions():
    """
    Check for expired subscriptions and update their status.
    Now includes 'cancelled' and 'suspended' subscriptions in the check.
    """
    import pytz
    from django.db.models import Count

    now_utc = timezone.now()                                      # always UTC internally
    ist     = pytz.timezone('Asia/Kolkata')
    now_ist = now_utc.astimezone(ist)

    logger.info("=" * 60)
    logger.info("CHECK_EXPIRED_SUBSCRIPTIONS TASK STARTED")
    logger.info(f"  now (UTC) : {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logger.info(f"  now (IST) : {now_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logger.info("-" * 60)

    # ── Step 0: Database Summary ──────────────────────────────────────────────
    status_summary = UserSubscription.objects.values('status').annotate(count=Count('id'))
    logger.info("Database Subscription Summary:")
    for entry in status_summary:
        logger.info(f"  {entry['status']:<10}: {entry['count']}")
    logger.info("-" * 60)

    # ── Step 1: Show ALL relevant subscriptions before filtering ─────────────
    # We now also look at cancelled and suspended since they should also officially "expire"
    all_eligible = UserSubscription.objects.filter(
        status__in=['active', 'trial', 'cancelled', 'suspended']
    ).select_related('user', 'plan').order_by('status', 'user__username')

    logger.info(f"Total eligible subscriptions in DB: {all_eligible.count()}")

    for sub in all_eligible:
        period_end_utc = sub.current_period_end
        period_end_ist = period_end_utc.astimezone(ist) if period_end_utc else None
        is_past        = period_end_utc < now_utc if period_end_utc else False

        logger.info(
            f"  SUB | user={sub.user.username:<15} "
            f"plan={sub.plan.name:<10} "
            f"status={sub.status:<10} "
            f"auto={str(sub.auto_renew):<6} "
            f"end_IST={period_end_ist.strftime('%Y-%m-%d %H:%M') if period_end_ist else 'None':<18} "
            f"is_past={str(is_past):<6}"
        )

    # ── Step 2: Find subscriptions whose period has ended ────────────────────
    # We include 'cancelled' and 'suspended' because even if they are already blocked, 
    # they should transition to the final 'expired' state once the time fully runs out.
    candidates = UserSubscription.objects.filter(
        current_period_end__lt=now_utc,
        status__in=['active', 'trial', 'cancelled', 'suspended'],
    ).select_related('user', 'plan')

    logger.info(f"Subscriptions with period_end < now: {candidates.count()}")

    if candidates.count() == 0:
        logger.info("RESULT: No new subscriptions to expire.")
        logger.info("Possible reasons:")
        logger.info("  1. current_period_end is still in the FUTURE")
        logger.info("  2. Subscriptions are ALREADY in 'expired' status")
        logger.info("  3. No eligible subscriptions exist (active/trial/cancelled/suspended)")
        logger.info("=" * 60)
        return "Marked 0 subscriptions as expired"

    # ── Step 3: Expire each candidate ────────────────────────────────────────
    expired_count = 0
    skipped_count = 0

    for subscription in candidates:
        try:
            period_end_ist = subscription.current_period_end.astimezone(ist)

            logger.info(
                f"EXPIRING: user={subscription.user.username} | "
                f"plan={subscription.plan.display_name} | "
                f"period_end={period_end_ist.strftime('%Y-%m-%d %H:%M IST')} | "
                f"auto_renew={subscription.auto_renew}"
            )

            subscription.status          = 'expired'
            subscription.tokens_remaining = 0
            subscription.bonus_tokens     = 0
            subscription.save(update_fields=['status', 'tokens_remaining', 'bonus_tokens'])
            expired_count += 1

            logger.info(f"  ✅ DONE — subscription {subscription.id} set to expired, tokens zeroed")

            # Send notification
            _send_task_notification(
                user=subscription.user,
                email_type='subscription_expired',
                subject=f'Your {subscription.plan.display_name} subscription has expired',
                context={
                    'plan_name': subscription.plan.display_name,
                    'renew_url': f"{django_settings.FRONTEND_URL}/pricing",
                    'plain_message': (
                        f"Hi {subscription.user.first_name or subscription.user.username},\n\n"
                        f"Your {subscription.plan.display_name} subscription has expired. "
                        f"Your tokens have been reset. Renew to regain access.\n\n"
                        f"Renew: {django_settings.FRONTEND_URL}/pricing"
                    ),
                    'log_metadata': {'subscription_id': str(subscription.id)},
                },
                template_name='emails/subscription_expired.html',
            )

            log_payment_event(
                'subscription.expired',
                subscription.user,
                subscription_id=str(subscription.id),
                plan=subscription.plan.display_name,
            )

        except Exception as e:
            skipped_count += 1
            logger.error(f"  ❌ ERROR expiring subscription {subscription.id}: {e}", exc_info=True)

    logger.info("=" * 60)
    logger.info(f"CHECK_EXPIRED_SUBSCRIPTIONS COMPLETE")
    logger.info(f"  Expired : {expired_count}")
    logger.info(f"  Errors  : {skipped_count}")
    logger.info("=" * 60)

    return f"Marked {expired_count} subscriptions as expired, {skipped_count} errors"

@shared_task
def check_trial_expirations():
    """
    Check for trial subscriptions that are expiring.
    
    Two phases:
    1. Send 'trial expiring' warning email to trials ending within 24 hours
    2. Expire trials that have passed their trial_ends_at date
    """
    from .models import EmailLog

    now = timezone.now()
    warning_window = now + timedelta(hours=24)

    # ── Phase 1: Warn trials expiring within 24 hours ──────────────────────
    expiring_soon = UserSubscription.objects.filter(
        is_trial=True,
        status='trial',
        trial_ends_at__gt=now,
        trial_ends_at__lte=warning_window,
    ).select_related('user', 'plan')

    warned_count = 0
    for subscription in expiring_soon:
        try:
            # Anti-duplicate: skip if we already warned this user recently
            already_warned = EmailLog.objects.filter(
                user=subscription.user,
                email_type='trial_expiring',
                created_at__gte=now - timedelta(days=1),
            ).exists()

            if already_warned:
                continue

            hours_remaining = int((subscription.trial_ends_at - now).total_seconds() / 3600)

            _send_task_notification(
                user=subscription.user,
                email_type='trial_expiring',
                subject=f'Your trial ends in {hours_remaining} hours',
                context={
                    'plan_name': subscription.plan.display_name,
                    'hours_remaining': hours_remaining,
                    'trial_ends_at': subscription.trial_ends_at,
                    'upgrade_url': f"{django_settings.FRONTEND_URL}/pricing",
                    'plain_message': (
                        f"Hi {subscription.user.first_name or subscription.user.username},\n\n"
                        f"Your {subscription.plan.display_name} trial ends in {hours_remaining} hours. "
                        f"After that, you'll lose access to your projects and tokens.\n\n"
                        f"Upgrade now to keep everything you've built: "
                        f"{django_settings.FRONTEND_URL}/pricing"
                    ),
                    'log_metadata': {'subscription_id': str(subscription.id)},
                },
                template_name='emails/trial_expiring.html',
            )

            warned_count += 1
            logger.info(f"📧 Sent trial expiring warning to {subscription.user.email} ({hours_remaining}h left)")

        except Exception as e:
            logger.error(f"Error sending trial expiring warning for {subscription.id}: {e}")

    # ── Phase 2: Expire trials that have ended ─────────────────────────────
    expired_trials = UserSubscription.objects.filter(
        is_trial=True,
        status='trial',
        trial_ends_at__lte=now
    ).select_related('user', 'plan')
    
    expired_count = 0
    for subscription in expired_trials:
        try:
            subscription.status = 'expired'
            subscription.tokens_remaining = 0
            subscription.bonus_tokens = 0
            subscription.save(update_fields=['status', 'tokens_remaining', 'bonus_tokens'])
            expired_count += 1

            logger.info(f"Trial expired for user {subscription.user.id}, tokens zeroed")

            # Send trial expired email
            _send_task_notification(
                user=subscription.user,
                email_type='trial_expired',
                subject='Your trial has ended',
                context={
                    'plan_name': subscription.plan.display_name,
                    'upgrade_url': f"{django_settings.FRONTEND_URL}/pricing",
                    'plain_message': (
                        f"Hi {subscription.user.first_name or subscription.user.username},\n\n"
                        f"Your {subscription.plan.display_name} trial has ended. "
                        f"Everything you built is still saved. Choose a plan to continue building.\n\n"
                        f"Choose a plan: {django_settings.FRONTEND_URL}/pricing"
                    ),
                    'log_metadata': {'subscription_id': str(subscription.id)},
                },
                template_name='emails/trial_expired.html',
            )
            
            logger.info(f"  📧 Sent trial expired email to {subscription.user.email}")

        except Exception as e:
            logger.error(f"Error processing trial expiration for {subscription.id}: {e}")
    
    return {
        'warned': warned_count,
        'expired': expired_count,
    }


@shared_task
def process_subscription_renewals():
    """
    Process automatic subscription renewals
    Should run daily
    """
    now = timezone.now()
    
    # Find subscriptions due for renewal in the next 24 hours
    due_renewals = UserSubscription.objects.filter(
        next_billing_date__lte=now + timedelta(hours=24),
        next_billing_date__gt=now,
        status='active',
        auto_renew=True
    )
    
    razorpay_service = RazorpayService()
    renewed_count = 0
    failed_count = 0
    
    for subscription in due_renewals:
        try:
            # Get subscription details from Razorpay
            if subscription.razorpay_subscription_id:
                result = razorpay_service.get_subscription(
                    subscription.razorpay_subscription_id
                )
                
                if result['success']:
                    razorpay_sub = result['subscription']
                    
                    # Check if subscription is still active in Razorpay
                    if razorpay_sub.get('status') == 'active':
                        # Reset monthly usage and allocate new tokens
                        subscription.reset_monthly_usage()
                        renewed_count += 1
                        
                        log_payment_event(
                            'subscription.renewed',
                            subscription.user,
                            subscription_id=str(subscription.id),
                            plan=subscription.plan.display_name,
                            tokens=subscription.plan.monthly_token_credits,
                        )

                        # Send renewal confirmation
                        _send_task_notification(
                            user=subscription.user,
                            email_type='subscription_renewed',
                            subject=f'Your {subscription.plan.display_name} subscription has been renewed',
                            context={
                                'plan_name': subscription.plan.display_name,
                                'tokens_allocated': subscription.plan.monthly_token_credits,
                                'billing_cycle': subscription.billing_cycle,
                                'next_renewal': subscription.current_period_end,
                                'plain_message': (
                                    f"Hi {subscription.user.first_name or subscription.user.username},\n\n"
                                    f"Your {subscription.plan.display_name} subscription has been renewed. "
                                    f"{subscription.plan.monthly_token_credits:,} tokens have been allocated "
                                    f"for this billing period.\n\n"
                                    f"Next renewal: {subscription.current_period_end.strftime('%B %d, %Y')}"
                                ),
                                'log_metadata': {
                                    'subscription_id': str(subscription.id),
                                    'tokens_allocated': subscription.plan.monthly_token_credits,
                                },
                            },
                            template_name='emails/subscription_renewed.html',
                        )
                    else:
                        subscription.status = 'cancelled'
                        subscription.save(update_fields=['status'])
                        failed_count += 1
                else:
                    failed_count += 1
        except Exception as e:
            failed_count += 1
            print(f"Error renewing subscription {subscription.id}: {e}")
    
    return {
        'renewed': renewed_count,
        'failed': failed_count
    }


@shared_task
def generate_usage_analytics():
    """
    Generate token usage analytics for all users
    Should run daily
    """
    from django.db.models import Sum, Count, Avg
    
    # Calculate overall statistics
    total_tokens_used = TokenUsage.objects.filter(
        status='success'
    ).aggregate(total=Sum('tokens_used'))['total'] or 0
    
    # Calculate per-user statistics
    active_users = UserSubscription.objects.filter(
        status__in=['active', 'trial']
    ).count()
    
    # Calculate average usage
    avg_daily_usage = TokenUsage.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=1),
        status='success'
    ).aggregate(avg=Avg('tokens_used'))['avg'] or 0
    
    return {
        'total_tokens_used': total_tokens_used,
        'active_users': active_users,
        'avg_daily_usage': round(avg_daily_usage, 2)
    }


@shared_task
def cleanup_old_usage_records():
    """
    Archive or delete old token usage records
    Keep records for 90 days
    Should run weekly
    """
    cutoff_date = timezone.now() - timedelta(days=90)
    
    # Delete old unsuccessful usage records
    deleted_count = TokenUsage.objects.filter(
        created_at__lt=cutoff_date,
        status='failed'
    ).delete()[0]
    
    return f"Deleted {deleted_count} old usage records"


@shared_task
def sync_razorpay_subscriptions():
    """
    Sync subscription status with Razorpay
    Should run every 6 hours
    """
    razorpay_service = RazorpayService()
    
    # Get all subscriptions with Razorpay IDs
    subscriptions = UserSubscription.objects.filter(
        razorpay_subscription_id__isnull=False
    ).exclude(status='cancelled')
    
    synced_count = 0
    cancelled_count = 0
    
    for subscription in subscriptions:
        try:
            result = razorpay_service.get_subscription(
                subscription.razorpay_subscription_id
            )
            
            if result['success']:
                razorpay_sub = result['subscription']
                razorpay_status = razorpay_sub.get('status')
                
                # Map Razorpay status to our status
                if razorpay_status == 'cancelled':
                    subscription.status = 'cancelled'
                    subscription.cancelled_at = timezone.now()
                    subscription.save()
                    cancelled_count += 1
                elif razorpay_status == 'active':
                    if subscription.status != 'active':
                        subscription.status = 'active'
                        subscription.save()
                        synced_count += 1
        except Exception as e:
            print(f"Error syncing subscription {subscription.id}: {e}")
    
    return {
        'synced': synced_count,
        'cancelled': cancelled_count
    }


@shared_task
def generate_monthly_invoices():
    """
    Generate invoices for successful payments without invoices
    Should run daily
    """
    payments_without_invoices = Payment.objects.filter(
        status='success',
        invoice_number=''
    )
    
    count = 0
    for payment in payments_without_invoices:
        payment._generate_invoice_number()
        count += 1
    
    return f"Generated {count} invoices"

@shared_task
def apply_scheduled_plan_changes():
    """
    Apply scheduled plan changes at renewal time
    Should run every hour
    """
    from django.utils import timezone
    from .models import UserSubscription, Payment
    
    now = timezone.now()
    
    # Find subscriptions with scheduled changes that have reached renewal
    subscriptions_to_change = UserSubscription.objects.filter(
        scheduled_plan__isnull=False,
        current_period_end__lte=now
    ).select_related('plan', 'scheduled_plan')
    
    success_count = 0
    error_count = 0
    
    for subscription in subscriptions_to_change:
        try:
            with transaction.atomic():
                old_plan_name = subscription.plan.display_name
                
                # Apply the scheduled change
                success, message = subscription.apply_scheduled_change()
                
                if success:
                    # Calculate new period
                    if subscription.billing_cycle == 'annual':
                        subscription.current_period_start = now
                        subscription.current_period_end = now + timedelta(days=365)
                        subscription.next_billing_date = now + timedelta(days=365)
                        amount = subscription.plan.annual_price
                    else:
                        subscription.current_period_start = now
                        subscription.current_period_end = now + timedelta(days=30)
                        subscription.next_billing_date = now + timedelta(days=30)
                        amount = subscription.plan.monthly_price
                    
                    subscription.save()
                    
                    # Create payment record for the new plan
                    Payment.objects.create(
                        user=subscription.user,
                        subscription=subscription,
                        payment_type='subscription',
                        amount=amount,
                        currency='INR',
                        status='pending',  # Will be updated by webhook
                        metadata={
                            'plan_id': str(subscription.plan.id),
                            'billing_cycle': subscription.billing_cycle,
                            'change_type': 'scheduled_downgrade',
                            'previous_plan': old_plan_name
                        }
                    )
                    
                    success_count += 1
                    
                    # In-app notification (low priority — not a payment event)
                    _create_in_app_notification(
                        user=subscription.user,
                        notification_type='plan_change_applied',
                        title=f'Plan changed to {subscription.plan.display_name}',
                        message=(
                            f"Your plan has been changed from {old_plan_name} to "
                            f"{subscription.plan.display_name}. "
                            f"You now have {subscription.plan.monthly_token_credits:,} tokens per month."
                        ),
                        metadata={
                            'old_plan': old_plan_name,
                            'new_plan': subscription.plan.display_name,
                            'new_tokens': subscription.plan.monthly_token_credits,
                        },
                    )

                    # Send email notification
                    _send_task_notification(
                        user=subscription.user,
                        email_type='plan_change_applied',
                        subject=f'Your plan has been updated to {subscription.plan.display_name}',
                        context={
                            'old_plan_name': old_plan_name,
                            'new_plan_name': subscription.plan.display_name,
                            'tokens_allocated': subscription.plan.monthly_token_credits,
                            'next_billing': subscription.current_period_end,
                            'plain_message': (
                                f"Hi {subscription.user.first_name or subscription.user.username},\n\n"
                                f"Your plan has been changed from {old_plan_name} to {subscription.plan.display_name}. "
                                f"You now have {subscription.plan.monthly_token_credits:,} tokens per month.\n\n"
                                f"Dashboard: {django_settings.FRONTEND_URL}/dashboard"
                            ),
                            'log_metadata': {
                                'subscription_id': str(subscription.id),
                                'old_plan': old_plan_name,
                                'new_plan': subscription.plan.display_name
                            },
                        },
                        template_name='emails/plan_change_applied.html',
                    )
                    
                    logger.info(f"Applied scheduled plan change for user {subscription.user.id}: {message}")
                    
                    log_payment_event(
                        'subscription.plan_changed',
                        subscription.user,
                        subscription_id=str(subscription.id),
                        plan=subscription.plan.display_name,
                        details={'previous_plan': old_plan_name},
                    )
                    
        except Exception as e:
            error_count += 1
            logger.error(f"Error applying scheduled change for subscription {subscription.id}: {str(e)}")
    
    return {
        'success': success_count,
        'errors': error_count,
        'message': f'Applied {success_count} scheduled plan changes, {error_count} errors'
    }


# REMOVED: check_failed_payment_grace_periods
# No grace period — payment failure = immediate suspension
# Handled directly in update_payment_status_on_subscription


@shared_task
def update_payment_status_on_subscription(payment_id, status):
    """
    Update subscription's last payment status.
    Called from payment verification views.

    NO GRACE PERIOD: Payment failure = immediate suspension + token zeroing.
    """
    try:
        payment = Payment.objects.select_related('subscription', 'subscription__user', 'subscription__plan').get(id=payment_id)
        
        if payment.subscription:
            subscription = payment.subscription
            subscription.last_payment_status = status
            
            if status == 'failed':
                subscription.failed_payment_count += 1

                # Immediate suspension — no grace period
                subscription.status = 'suspended'
                subscription.tokens_remaining = 0
                subscription.bonus_tokens = 0
                subscription.save(update_fields=[
                    'last_payment_status', 'failed_payment_count',
                    'status', 'tokens_remaining', 'bonus_tokens',
                ])

                # HIGH PRIORITY email — user lost access
                _send_task_notification(
                    user=subscription.user,
                    email_type='subscription_suspended',
                    subject='Your dm-me subscription has been suspended',
                    context={
                        'plan_name': subscription.plan.display_name,
                        'failed_count': subscription.failed_payment_count,
                        'reactivate_url': f"{django_settings.FRONTEND_URL}/pricing",
                        'plain_message': (
                            f"Hi {subscription.user.first_name or subscription.user.username},\n\n"
                            f"Your payment for {subscription.plan.display_name} failed. "
                            f"Your subscription has been suspended and tokens have been reset.\n\n"
                            f"Update your payment method to reactivate: "
                            f"{django_settings.FRONTEND_URL}/pricing"
                        ),
                        'log_metadata': {
                            'subscription_id': str(subscription.id),
                            'failed_count': subscription.failed_payment_count,
                        },
                    },
                    template_name='emails/subscription_suspended.html',
                )

                log_payment_event(
                    'subscription.suspended',
                    subscription.user,
                    subscription_id=str(subscription.id),
                    plan=subscription.plan.display_name,
                    details={
                        'reason': 'payment_failed',
                        'failed_count': subscription.failed_payment_count,
                    },
                )

                logger.info(
                    f"Payment failed → subscription {subscription.id} suspended immediately, "
                    f"tokens zeroed"
                )
                    
            elif status == 'success':
                # Reset failed payment count
                subscription.failed_payment_count = 0
                subscription.save(update_fields=[
                    'last_payment_status', 'failed_payment_count',
                ])
            
            logger.info(f"Updated payment status for subscription {subscription.id}: {status}")
            
    except Payment.DoesNotExist:
        logger.error(f"Payment {payment_id} not found")
    except Exception as e:
        logger.error(f"Error updating payment status: {str(e)}")


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=300,
)
def auto_purchase_tokens(self, user_id, package_id):
    """
    Automatically purchase tokens for a user via their saved payment method.

    Flow:
    1. Find user's default saved PaymentMethod
    2. Create a Razorpay order
    3. Attempt to charge via Razorpay recurring payment API
    4. If charge succeeds → mark payment success, add tokens
    5. If charge fails → mark payment failed, notify user
    6. If no saved payment method → skip, notify user to add one

    If Razorpay recurring/auto-debit is not yet set up, falls back to
    creating a pending payment and notifying the user to complete checkout.
    """
    from django.contrib.auth.models import User
    from .models import TokenPackage, Payment, UserSubscription, TokenUsage, PaymentMethod
    from .razorpay_service import RazorpayService

    try:
        user = User.objects.get(id=user_id)
        package = TokenPackage.objects.get(id=package_id)
        subscription = UserSubscription.objects.get(user=user, status__in=['active', 'trial'])

        # Step 1: Find saved payment method
        saved_method = PaymentMethod.objects.filter(
            user=user,
            is_active=True,
            is_default=True,
        ).first()

        if not saved_method:
            # No saved payment method — can't auto-charge
            # Fall back: create pending payment + notify user
            logger.warning(
                f"Auto-refill for user {user.id}: No saved payment method. "
                f"Creating pending payment for manual completion."
            )

            razorpay_service = RazorpayService()
            amount = package.get_price_for_currency('INR')

            order_result = razorpay_service.create_order(
                amount=amount,
                currency='INR',
                receipt=f'autorefill_{user.id}_{int(timezone.now().timestamp())}',
                notes={
                    'user_id': str(user.id),
                    'package_id': str(package.id),
                    'auto_refill': True,
                    'token_count': package.get_total_tokens(),
                }
            )

            if order_result.get('success'):
                Payment.objects.create(
                    user=user,
                    subscription=subscription,
                    payment_type='token_purchase',
                    amount=amount,
                    currency='INR',
                    razorpay_order_id=order_result['order']['id'],
                    tokens_purchased=package.get_total_tokens(),
                    status='pending',
                    metadata={
                        'auto_refill': True,
                        'package_id': str(package.id),
                        'package_name': package.name,
                        'requires_manual_payment': True,
                    }
                )

            # TODO: Send email — "Your tokens are low, complete payment to refill"
            # from .receipt.email_tasks import send_auto_refill_reminder_email
            # send_auto_refill_reminder_email.delay(str(user.id), str(package.id))

            return {
                'success': False,
                'reason': 'no_saved_payment_method',
                'user_id': user_id,
            }

        # Step 2: Create Razorpay order
        razorpay_service = RazorpayService()
        amount = package.get_price_for_currency('INR')

        order_result = razorpay_service.create_order(
            amount=amount,
            currency='INR',
            receipt=f'autorefill_{user.id}_{int(timezone.now().timestamp())}',
            notes={
                'user_id': str(user.id),
                'package_id': str(package.id),
                'auto_refill': True,
                'saved_method_id': str(saved_method.id),
            }
        )

        if not order_result.get('success'):
            raise Exception(f"Razorpay order creation failed: {order_result.get('error')}")

        order = order_result['order']

        # Step 3: Create payment record as PENDING
        payment = Payment.objects.create(
            user=user,
            subscription=subscription,
            payment_type='token_purchase',
            amount=amount,
            currency='INR',
            razorpay_order_id=order['id'],
            tokens_purchased=package.get_total_tokens(),
            status='pending',
            metadata={
                'auto_refill': True,
                'package_id': str(package.id),
                'package_name': package.name,
                'saved_method_id': str(saved_method.id),
                'saved_method_type': saved_method.method_type,
            }
        )

        # Step 4: Attempt to charge via Razorpay recurring payment
        # NOTE: This requires Razorpay recurring payments to be enabled
        # on your account and the customer to have authorized recurring.
        # If not available, the payment stays pending and user is notified.
        try:
            charge_result = razorpay_service.client.payment.create_recurring_payment({
                'email': user.email,
                'contact': getattr(user, 'phone', ''),
                'type': 'auto',
                'token': saved_method.razorpay_payment_id,
                'customer_id': subscription.razorpay_customer_id,
                'order_id': order['id'],
                'amount': int(amount * 100),  # Razorpay expects paise
                'currency': 'INR',
                'description': f'Auto-refill: {package.name}',
            })

            if charge_result.get('razorpay_payment_id'):
                # Charge initiated — Razorpay will send webhook for final status
                payment.razorpay_payment_id = charge_result['razorpay_payment_id']
                payment.metadata['charge_initiated'] = True
                payment.save()

                logger.info(
                    f"Auto-refill charge initiated for user {user.id}: "
                    f"payment {charge_result['razorpay_payment_id']}"
                )

                return {
                    'success': True,
                    'status': 'charge_initiated',
                    'payment_id': str(payment.id),
                    'user_id': user_id,
                }

        except Exception as charge_error:
            # Recurring charge not available or failed
            # Payment stays pending — user needs to complete manually
            logger.warning(
                f"Auto-refill recurring charge failed for user {user.id}: {charge_error}. "
                f"Payment {payment.id} left as pending for manual completion."
            )

            payment.metadata['recurring_charge_error'] = str(charge_error)
            payment.save()

            # TODO: Send email — "Auto-refill couldn't charge, please complete payment"
            # from .receipt.email_tasks import send_auto_refill_failed_email
            # send_auto_refill_failed_email.delay(str(user.id), str(payment.id))

            return {
                'success': False,
                'reason': 'recurring_charge_failed',
                'error': str(charge_error),
                'payment_id': str(payment.id),
                'user_id': user_id,
            }

    except User.DoesNotExist:
        logger.error(f"Auto-refill: User {user_id} not found")
        return {'success': False, 'reason': 'user_not_found'}

    except TokenPackage.DoesNotExist:
        logger.error(f"Auto-refill: Package {package_id} not found")
        return {'success': False, 'reason': 'package_not_found'}

    except UserSubscription.DoesNotExist:
        logger.error(f"Auto-refill: No active subscription for user {user_id}")
        return {'success': False, 'reason': 'no_active_subscription'}

    except Exception as e:
        logger.error(f"Auto-refill failed for user {user_id}: {e}", exc_info=True)
        # Retry on transient errors (network, Razorpay downtime)
        raise self.retry(exc=e)

# @shared_task
# def auto_purchase_tokens(user_id, package_id):
#     """Automatically purchase tokens for user"""
#     from django.contrib.auth.models import User
#     from .models import TokenPackage, Payment, UserSubscription, TokenUsage
#     from .razorpay_service import RazorpayService

#     try:
#         user = User.objects.get(id=user_id)
#         package = TokenPackage.objects.get(id=package_id)
#         subscription = UserSubscription.objects.get(user=user)

#         # For auto-refill, directly add tokens without payment processing
#         # Create payment record as completed
#         payment = Payment.objects.create(
#             user=user,
#             subscription=subscription,
#             payment_type='token_purchase',
#             amount=package.price_inr,
#             currency='INR',
#             tokens_purchased=package.get_total_tokens(),
#             status='success',
#             completed_at=timezone.now(),
#             metadata={
#                 'auto_refill': True,
#                 'package_id': str(package.id)
#             }
#         )

#         # Add tokens to subscription
#         total_tokens = package.get_total_tokens()
#         subscription.add_bonus_tokens(total_tokens)

#         # Create token usage record for the purchase
#         TokenUsage.objects.create(
#             user=user,
#             subscription=subscription,
#             tokens_used=0,
#             tokens_requested=0,
#             description=f"Auto-refill: {package.name}",
#             status='success',
#             feature='auto_refill'
#         )

#         # Send notification to user about auto-purchase
#         # (implement notification system)

#     except Exception as e:
#         logger.error(f"Auto refill failed for user {user_id}: {e}")


# REMOVED: retry_failed_payments (dunning system)
# No grace period — payment failure = immediate suspension.
# No need for escalating dunning emails over 7 days.


# ==========================================
# CHANGE 16 — cleanup_stale_pending_payments
# ==========================================

@shared_task
def cleanup_stale_pending_payments():
    """
    Mark abandoned 'pending' payments as 'expired'.

    Runs every hour via Celery Beat.

    Why this matters:
    - Change 3 made PurchaseTokensView create payments as 'pending'
    - CreateSubscriptionView already creates as 'pending'
    - If user abandons Razorpay checkout, payment stays 'pending' forever
    - Razorpay orders expire after ~30 min, but our DB doesn't know that
    - This task cleans up any pending payments older than 2 hours

    Excludes:
    - Payments with metadata.requires_manual_payment (auto-refill waiting for user)
    - Payments less than 2 hours old (user might still be in checkout)
    """
    cutoff = timezone.now() - timedelta(hours=2)

    # Find stale pending payments
    stale_candidates = Payment.objects.filter(
        status='pending',
        created_at__lt=cutoff,
    ).only('id', 'metadata')

    pids_to_expire = []
    for p in stale_candidates:
        if not p.metadata.get('requires_manual_payment'):
            pids_to_expire.append(p.id)

    if not pids_to_expire:
        logger.info("No stale pending payments to clean up")
        return {'expired': 0}

    # Bulk update to expired
    expired_count = Payment.objects.filter(id__in=pids_to_expire).update(
        status='expired',
        failure_reason='Payment abandoned — Razorpay order expired (auto-cleanup)',
    )

    logger.info(f"Expired {expired_count} stale pending payments (older than 2 hours)")

    return {
        'expired': expired_count,
        'cutoff': cutoff.isoformat(),
    }

@shared_task
def send_downgrade_warnings():
    """
    Warn users about upcoming scheduled downgrades 3 days before they happen.
    Uses in-app notification (not email — low priority).
    """
    from .models import UserSubscription

    now = timezone.now()
    warning_window = now + timedelta(days=3)

    upcoming_changes = UserSubscription.objects.filter(
        scheduled_plan__isnull=False,
        current_period_end__lte=warning_window,
        current_period_end__gt=now,
        status='active',
    ).select_related('user', 'plan', 'scheduled_plan')

    sent_count = 0
    skip_count = 0
    error_count = 0

    for sub in upcoming_changes:
        try:
            # Anti-duplicate: check if we already warned recently
            from .models import EmailLog
            already_warned = EmailLog.objects.filter(
                user=sub.user,
                email_type='subscription_reminder',
                created_at__gte=now - timedelta(days=7),
                metadata__warning_type='downgrade_warning',
                metadata__scheduled_plan_id=str(sub.scheduled_plan.id),
            ).exists()

            if already_warned:
                skip_count += 1
                continue

            will_lose, tokens_to_lose = sub.check_token_loss(sub.scheduled_plan)
            days_until_change = (sub.current_period_end - now).days

            title = (
                f'Plan changes to {sub.scheduled_plan.display_name} '
                f'in {days_until_change} days'
            )
            if will_lose:
                title = (
                    f'You\'ll lose {tokens_to_lose:,} tokens in '
                    f'{days_until_change} days — use them now'
                )

            _create_in_app_notification(
                user=sub.user,
                notification_type='downgrade_warning',
                title=title,
                message=(
                    f"Your plan will change from {sub.plan.display_name} "
                    f"to {sub.scheduled_plan.display_name} on "
                    f"{sub.current_period_end.strftime('%B %d, %Y')}."
                    + (f" You will lose {tokens_to_lose:,} tokens. "
                       f"Use them before the switch!"
                       if will_lose else "")
                ),
                metadata={
                    'current_plan': sub.plan.display_name,
                    'new_plan': sub.scheduled_plan.display_name,
                    'days_until_change': days_until_change,
                    'tokens_to_lose': tokens_to_lose,
                },
            )

            # Log to prevent re-sending (reuse EmailLog for dedup tracking)
            EmailLog.objects.create(
                user=sub.user,
                email_type='subscription_reminder',
                recipient='in-app',
                subject=title,
                status='sent',
                metadata={
                    'warning_type': 'downgrade_warning',
                    'scheduled_plan_id': str(sub.scheduled_plan.id),
                    'days_until_change': days_until_change,
                    'tokens_to_lose': tokens_to_lose,
                    'delivery_method': 'in_app',
                }
            )

            sent_count += 1
            logger.info(
                f"Downgrade warning (in-app) for {sub.user.email}: "
                f"{sub.plan.display_name} → {sub.scheduled_plan.display_name} "
                f"in {days_until_change} days"
            )

        except Exception as e:
            error_count += 1
            logger.error(f"Error processing downgrade warning for sub {sub.id}: {e}")

    logger.info(
        f"Downgrade warnings: {sent_count} sent (in-app), "
        f"{skip_count} skipped, {error_count} errors"
    )

    return {
        'sent': sent_count,
        'skipped': skip_count,
        'errors': error_count,
    }

@shared_task
def generate_monthly_billing_report():
    """
    Generate a comprehensive billing report for the previous month.
    Emails the report to admins.

    Runs on the 1st of each month at 7 AM via Celery Beat.

    Metrics:
    - Total revenue (successful payments)
    - New subscriptions created
    - Subscriptions cancelled (churn)
    - Total tokens consumed
    - Active subscribers count
    - Revenue by plan
    - Top token consumers
    - Failed payment count
    """
    from django.db.models import Sum, Count, Avg, Q
    from django.db.models.functions import TruncDate
    from django.core.mail import send_mail
     
    from .models import UserSubscription, Payment, TokenUsage

    now = timezone.now()

    # Previous month boundaries
    first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_end = first_of_this_month - timedelta(seconds=1)
    last_month_start = last_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    month_name = last_month_start.strftime('%B %Y')

    # ── Revenue ──
    revenue = Payment.objects.filter(
        status='success',
        completed_at__gte=last_month_start,
        completed_at__lt=first_of_this_month,
    ).aggregate(
        total=Sum('amount'),
        count=Count('id'),
        avg=Avg('amount'),
    )

    # Revenue by payment type
    revenue_by_type = Payment.objects.filter(
        status='success',
        completed_at__gte=last_month_start,
        completed_at__lt=first_of_this_month,
    ).values('payment_type').annotate(
        total=Sum('amount'),
        count=Count('id'),
    ).order_by('-total')

    # ── Subscriptions ──
    new_subs = UserSubscription.objects.filter(
        start_date__gte=last_month_start,
        start_date__lt=first_of_this_month,
    ).count()

    cancelled_subs = UserSubscription.objects.filter(
        cancelled_at__gte=last_month_start,
        cancelled_at__lt=first_of_this_month,
    ).count()

    active_subs = UserSubscription.objects.filter(
        status='active',
    ).count()

    trial_subs = UserSubscription.objects.filter(
        status='trial',
    ).count()

    # Subs by plan
    subs_by_plan = UserSubscription.objects.filter(
        status='active',
    ).values('plan__display_name').annotate(
        count=Count('id'),
    ).order_by('-count')

    # ── Tokens ──
    token_stats = TokenUsage.objects.filter(
        created_at__gte=last_month_start,
        created_at__lt=first_of_this_month,
        status='success',
    ).aggregate(
        total_consumed=Sum('tokens_used'),
        total_requests=Count('id'),
    )

    # ── Failed Payments ──
    failed_payments = Payment.objects.filter(
        status='failed',
        created_at__gte=last_month_start,
        created_at__lt=first_of_this_month,
    ).aggregate(
        count=Count('id'),
        total_amount=Sum('amount'),
    )

    # ── MRR (Monthly Recurring Revenue) ──
    monthly_mrr = UserSubscription.objects.filter(
        status='active', billing_cycle='monthly'
    ).aggregate(total=Sum('plan__monthly_price'))['total'] or Decimal('0')

    annual_mrr = UserSubscription.objects.filter(
        status='active', billing_cycle='annual'
    ).aggregate(total=Sum('plan__annual_price'))['total'] or Decimal('0')
    
    mrr = monthly_mrr + (annual_mrr / 12)

    # ── Churn Rate ──
    start_of_month_active = active_subs + cancelled_subs  # approximate
    churn_rate = (
        (cancelled_subs / start_of_month_active * 100)
        if start_of_month_active > 0 else 0
    )

    # ── Build Report ──
    report_data = {
        'month': month_name,
        'revenue': {
            'total': float(revenue['total'] or 0),
            'count': revenue['count'],
            'average': float(revenue['avg'] or 0),
            'by_type': list(revenue_by_type),
        },
        'subscriptions': {
            'new': new_subs,
            'cancelled': cancelled_subs,
            'active': active_subs,
            'trial': trial_subs,
            'by_plan': list(subs_by_plan),
            'churn_rate': round(churn_rate, 2),
        },
        'tokens': {
            'total_consumed': token_stats['total_consumed'] or 0,
            'total_requests': token_stats['total_requests'] or 0,
        },
        'failed_payments': {
            'count': failed_payments['count'],
            'total_amount': float(failed_payments['total_amount'] or 0),
        },
        'mrr': float(mrr),
    }

    # ── Format Email ──
    plan_breakdown = '\n'.join(
        f"  {p['plan__display_name']}: {p['count']} subscribers"
        for p in subs_by_plan
    )

    type_breakdown = '\n'.join(
        f"  {t['payment_type']}: ${t['total']:.2f} ({t['count']} payments)"
        for t in revenue_by_type
    )

    report_text = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  dm-me — Monthly Billing Report
  {month_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REVENUE
  Total:     ${report_data['revenue']['total']:,.2f}
  Payments:  {report_data['revenue']['count']}
  Average:   ${report_data['revenue']['average']:,.2f}
  MRR:       ${report_data['mrr']:,.2f}

  By Type:
{type_breakdown}

SUBSCRIPTIONS
  New:        {new_subs}
  Cancelled:  {cancelled_subs}
  Active:     {active_subs}
  Trial:      {trial_subs}
  Churn Rate: {churn_rate:.1f}%

  By Plan:
{plan_breakdown}

TOKEN USAGE
  Total Consumed: {report_data['tokens']['total_consumed']:,}
  Total Requests: {report_data['tokens']['total_requests']:,}

FAILED PAYMENTS
  Count:  {failed_payments['count']}
  Amount: ${report_data['failed_payments']['total_amount']:,.2f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generated: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}
"""

    # ── Send to Admins ──
    admin_emails = [email for name, email in django_settings.ADMINS] if django_settings.ADMINS else []

    if admin_emails:
        try:
            send_mail(
                subject=f'dm-me Billing Report — {month_name}',
                message=report_text,
                from_email=django_settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                fail_silently=False,
            )
            logger.info(f"Monthly billing report sent to {admin_emails}")
        except Exception as e:
            logger.error(f"Failed to send billing report email: {e}")
    else:
        logger.warning(
            "No ADMINS configured in settings.py — billing report not emailed. "
            "Add ADMINS = [('Name', 'email@example.com')] to settings."
        )

    logger.info(f"Monthly billing report for {month_name}: {report_data}")

    return report_data

@shared_task
def expire_unused_referral_credits():
    """
    Expire referral bonus tokens that were awarded more than 90 days ago
    and haven't been fully consumed.

    Runs weekly (Monday 2 AM) via Celery Beat.

    Logic:
    1. Find Referral records where rewards_processed=True
       and created_at < 90 days ago
    2. For each, check if the referrer/referee still has bonus_tokens > 0
    3. Deduct the original referral award amount from bonus_tokens
       (but never go below 0)
    4. Mark the referral as expired so we don't re-process it

    Why 90 days:
    - Long enough for legitimate users to consume their bonus
    - Short enough to prevent indefinite token hoarding
    - Matches industry standard for promotional credits

    Important: This deducts from bonus_tokens (the overall pool),
    NOT from specific tracked referral tokens. There's no per-source
    tracking on bonus_tokens, so we deduct the originally awarded amount.
    If the user already consumed those tokens, their bonus_tokens may
    already be 0 and nothing happens.
    """
    from django.db.models import F
    from .models import Referral, UserSubscription

    now = timezone.now()
    cutoff = now - timedelta(days=90)

    EXPIRY_DAYS = 90

    # Find referrals that were processed, are older than 90 days,
    # and haven't been marked as expired yet
    expired_referrals = Referral.objects.filter(
        rewards_processed=True,
        created_at__lt=cutoff,
    ).exclude(
        # Skip already-expired ones. We'll use a metadata convention:
        # if referrer_tokens_awarded is negative, it means we already expired it.
        # But that's hacky. Instead, let's just check if we processed it by
        # looking for a specific pattern. Since the model has no 'expired' field,
        # we'll track via a simple approach: only process referrals where
        # awarded tokens are > 0 (meaning we haven't zeroed them out yet).
        referrer_tokens_awarded=0,
        referee_tokens_awarded=0,
    ).select_related('referrer', 'referee', 'referral_code')

    expired_count = 0
    tokens_reclaimed = 0
    errors = 0

    for referral in expired_referrals:
        try:
            # Expire referrer's bonus
            if referral.referrer_tokens_awarded > 0:
                referrer_sub = UserSubscription.objects.filter(
                    user=referral.referrer,
                    status__in=['active', 'trial'],
                ).first()

                if referrer_sub and referrer_sub.bonus_tokens > 0:
                    deduct = min(referral.referrer_tokens_awarded, referrer_sub.bonus_tokens)

                    UserSubscription.objects.filter(id=referrer_sub.id).update(
                        bonus_tokens=F('bonus_tokens') - deduct,
                        tokens_remaining=F('tokens_remaining') - deduct,
                    )

                    tokens_reclaimed += deduct

                    logger.info(
                        f"Expired {deduct} referral bonus tokens for "
                        f"referrer {referral.referrer.username} "
                        f"(referral from {referral.created_at.date()})"
                    )

            # Expire referee's bonus
            if referral.referee_tokens_awarded > 0:
                referee_sub = UserSubscription.objects.filter(
                    user=referral.referee,
                    status__in=['active', 'trial'],
                ).first()

                if referee_sub and referee_sub.bonus_tokens > 0:
                    deduct = min(referral.referee_tokens_awarded, referee_sub.bonus_tokens)

                    UserSubscription.objects.filter(id=referee_sub.id).update(
                        bonus_tokens=F('bonus_tokens') - deduct,
                        tokens_remaining=F('tokens_remaining') - deduct,
                    )

                    tokens_reclaimed += deduct

                    logger.info(
                        f"Expired {deduct} referral bonus tokens for "
                        f"referee {referral.referee.username} "
                        f"(referral from {referral.created_at.date()})"
                    )

            # Mark referral as expired by zeroing out awarded amounts
            # This prevents re-processing on next run
            referral.referrer_tokens_awarded = 0
            referral.referee_tokens_awarded = 0
            referral.save(update_fields=['referrer_tokens_awarded', 'referee_tokens_awarded'])

            log_payment_event(
                'tokens.expired',
                referral.referrer,
                tokens=tokens_reclaimed,
                details={'type': 'referral_expiry', 'referral_id': str(referral.id)},
            )

            expired_count += 1

        except Exception as e:
            errors += 1
            logger.error(f"Error expiring referral {referral.id}: {e}")

    logger.info(
        f"Referral credit expiry: {expired_count} referrals processed, "
        f"{tokens_reclaimed:,} tokens reclaimed, {errors} errors"
    )

    return {
        'expired_referrals': expired_count,
        'tokens_reclaimed': tokens_reclaimed,
        'errors': errors,
    }

@shared_task
def check_low_token_balances():
    """
    Identify users with low token balances and send in-app notifications.
    Low priority — no email.
    """
    low_balance_users = []
    
    for subscription in UserSubscription.objects.filter(
        status__in=['active', 'trial']
    ).select_related('user', 'plan'):
        if subscription.plan.monthly_token_credits > 0:
            percentage = (subscription.tokens_remaining / subscription.plan.monthly_token_credits) * 100
            
            if percentage < 10:
                low_balance_users.append({
                    'user_id': subscription.user.id,
                    'tokens_remaining': subscription.tokens_remaining,
                    'percentage': round(percentage, 1)
                })

                _create_in_app_notification(
                    user=subscription.user,
                    notification_type='low_token_balance',
                    title=f'Running low on tokens ({round(percentage, 1)}% remaining)',
                    message=(
                        f"You have {subscription.tokens_remaining:,} tokens remaining "
                        f"({round(percentage, 1)}% of your plan). "
                        f"Purchase more tokens to avoid interruptions."
                    ),
                    metadata={
                        'tokens_remaining': subscription.tokens_remaining,
                        'percentage': round(percentage, 1),
                    },
                )

    return {
        'count': len(low_balance_users),
        'users': low_balance_users,
    }

@shared_task
def detect_suspicious_token_activity():
    """
    Flag accounts with abnormally high token consumption.
    Runs every 4 hours via Celery Beat.
    """
    from django.db.models import Sum

    now = timezone.now()
    four_hours_ago = now - timedelta(hours=4)
    thirty_days_ago = now - timedelta(days=30)

    SPIKE_MULTIPLIER = 5
    MIN_THRESHOLD = 1000

    flagged_users = []

    active_subs = UserSubscription.objects.filter(
        status__in=['active', 'trial'],
    ).select_related('user', 'plan')

    for sub in active_subs:
        try:
            total_30d = TokenUsage.objects.filter(
                user=sub.user,
                created_at__gte=thirty_days_ago,
                status='success',
            ).aggregate(total=Sum('tokens_used'))['total'] or 0

            daily_avg = total_30d / 30 if total_30d > 0 else 0

            recent_usage = TokenUsage.objects.filter(
                user=sub.user,
                created_at__gte=four_hours_ago,
                status='success',
            ).aggregate(total=Sum('tokens_used'))['total'] or 0

            if recent_usage > MIN_THRESHOLD and daily_avg > 0:
                if recent_usage > (daily_avg * SPIKE_MULTIPLIER):
                    flagged_users.append({
                        'user_id': sub.user.id,
                        'username': sub.user.username,
                        'email': sub.user.email,
                        'plan': sub.plan.display_name,
                        'daily_average': round(daily_avg),
                        'last_4h_usage': recent_usage,
                        'multiplier': round(recent_usage / daily_avg, 1),
                    })
                    logger.warning(
                        f"SUSPICIOUS TOKEN ACTIVITY: {sub.user.username} "
                        f"({sub.user.email}) used {recent_usage:,} tokens in 4h "
                        f"(daily avg: {daily_avg:,.0f}, {recent_usage/daily_avg:.1f}x spike)"
                    )
        except Exception as e:
            logger.error(f"Error checking suspicious activity for user {sub.user.id}: {e}")

    if flagged_users:
        from django.core.mail import send_mail
        admin_emails = [email for _, email in django_settings.ADMINS] if django_settings.ADMINS else []
        if admin_emails:
            user_lines = '\\n'.join(
                f"  - {u['username']} ({u['email']}): "
                f"{u['last_4h_usage']:,} tokens in 4h ({u['multiplier']}x daily avg)"
                for u in flagged_users
            )
            try:
                send_mail(
                    subject=f'Suspicious Token Activity — {len(flagged_users)} accounts flagged',
                    message=f"Flagged accounts:\\n\\n{user_lines}\\n\\nReview manually.",
                    from_email=django_settings.DEFAULT_FROM_EMAIL,
                    recipient_list=admin_emails,
                    fail_silently=True,
                )
            except Exception as e:
                logger.error(f"Failed to send suspicious activity alert: {e}")

    logger.info(f"Suspicious activity check: {len(flagged_users)} flagged out of {active_subs.count()}")
    return {'flagged': len(flagged_users), 'total_checked': active_subs.count()}

@shared_task
def calculate_revenue_metrics():
    """
    Calculate revenue metrics for analytics
    Should run daily
    """
    from django.db.models import Sum
    
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Today's revenue
    today_revenue = Payment.objects.filter(
        status='success',
        completed_at__gte=today_start
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Month's revenue
    month_revenue = Payment.objects.filter(
        status='success',
        completed_at__gte=month_start
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Active subscriptions
    active_subs = UserSubscription.objects.filter(status='active').count()
    trial_subs = UserSubscription.objects.filter(status='trial').count()
    
    # MRR (Monthly Recurring Revenue)
    mrr = UserSubscription.objects.filter(
        status='active',
        billing_cycle='monthly'
    ).aggregate(total=Sum('plan__monthly_price'))['total'] or Decimal('0.00')
    
    return {
        'today_revenue': float(today_revenue),
        'month_revenue': float(month_revenue),
        'active_subscriptions': active_subs,
        'trial_subscriptions': trial_subs,
        'mrr': float(mrr)
    }