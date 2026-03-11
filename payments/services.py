"""
Subscription Service for AI Platform
Handles subscription lifecycle: creation, upgrades, and validations.
"""
import logging
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from .models import UserSubscription, SubscriptionPlan, Payment
from .audit import log_payment_event

logger = logging.getLogger(__name__)

class SubscriptionService:
    @staticmethod
    def create_initial_free_subscription(user):
        """
        Creates a fundamental FREE subscription for a new user.
        Uses a one-time token allocation from the 'free' plan.
        """
        try:
            with transaction.atomic():
                # Check if subscription already exists to prevent duplicates
                if UserSubscription.objects.filter(user=user).exists():
                    logger.info(f"User {user.email} already has a subscription.")
                    return None

                # Get free plan
                free_plan = SubscriptionPlan.objects.get(name='free')
                
                subscription = UserSubscription.objects.create(
                    user=user,
                    plan=free_plan,
                    billing_cycle='monthly',
                    status='active',
                    is_trial=False,
                    trial_ends_at=None,
                    current_period_start=timezone.now(),
                    current_period_end=timezone.now() + timedelta(days=30),
                    auto_renew=False
                )

                logger.info(f"✅ Created FREE subscription for {user.username}")
                return subscription

        except SubscriptionPlan.DoesNotExist:
            logger.error("❌ 'free' SubscriptionPlan not found in database!")
            return None
        except Exception as e:
            logger.error(f"❌ Error creating free subscription for {user.username}: {e}")
            return None

    @staticmethod
    def validate_plan_change(subscription, new_plan, new_billing_cycle='monthly'):
        """
        Validates if a user can switch to a new plan.
        Returns: (can_change: bool, reason: str, is_upgrade: bool)
        """
        return subscription.can_change_plan(new_plan, new_billing_cycle)

    @staticmethod
    def activate_subscription(payment, razorpay_payment_id, razorpay_signature=None, ip_address=None):
        """
        Core logic to activate a subscription after a guaranteed successful payment.
        Returns: tuple(success: bool, result_data: dict, payment: Payment)
        """
        try:
            plan_id = payment.metadata.get('plan_id')
            billing_cycle = payment.metadata.get('billing_cycle', 'monthly')
            user = payment.user
            
            plan = SubscriptionPlan.objects.get(id=plan_id)
            
            # Calculate period
            period_start = timezone.now()
            if billing_cycle == 'annual':
                period_end = period_start + timedelta(days=365)
            else:
                period_end = period_start + timedelta(days=30)
                
            with transaction.atomic():
                try:
                    existing_subscription = UserSubscription.objects.select_for_update().select_related('plan').get(user=user)
                    is_upgrade = True
                    existing_plan_name = existing_subscription.plan.display_name
                except UserSubscription.DoesNotExist:
                    is_upgrade = False
                    existing_plan_name = None

                subscription, created = UserSubscription.objects.update_or_create(
                    user=user,
                    defaults={
                        'plan': plan,
                        'billing_cycle': billing_cycle,
                        'status': 'active',
                        'current_period_start': period_start,
                        'current_period_end': period_end,
                        'next_billing_date': period_end,
                        'auto_renew': True,
                        'is_trial': False,
                        'last_payment_status': 'success',
                        'failed_payment_count': 0
                    }
                )

                payment.subscription = subscription
                payment.razorpay_payment_id = razorpay_payment_id
                if razorpay_signature:
                    payment.razorpay_signature = razorpay_signature
                payment.status = 'success'
                payment.completed_at = timezone.now()
                payment.metadata.update({
                    'is_upgrade': is_upgrade,
                    'previous_plan': existing_plan_name,
                })
                
                if not payment.invoice_number:
                    payment.generate_invoice_number()
                payment.save()

                log_payment_event(
                    'subscription.created' if not is_upgrade else 'subscription.upgraded',
                    user,
                    subscription_id=str(subscription.id),
                    payment_id=str(payment.id),
                    plan=plan.display_name,
                    amount=float(payment.amount),
                    ip_address=ip_address,
                    details={'billing_cycle': billing_cycle},
                )

            # Outside atomic transaction
            try:
                from .receipt.email_tasks import send_payment_receipt_email
                logger.info(f"Queuing payment receipt email for payment {payment.id}")
                send_payment_receipt_email.delay(str(payment.id))
            except Exception as email_error:
                logger.error(f"Failed to queue receipt email: {str(email_error)}")

            result_data = {
                'id': str(subscription.id),
                'plan': plan.display_name,
                'status': subscription.status,
                'billing_cycle': billing_cycle,
                'is_upgrade': is_upgrade,
                'period_end': period_end.isoformat()
            }
            return True, result_data, payment

            
        except Exception as e:
            logger.error(f"activate_subscription failed: {str(e)}", exc_info=True)
            return False, str(e), None

