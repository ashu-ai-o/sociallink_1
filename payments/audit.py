"""
Payment Audit Logger
payments/audit.py

Logs all payment events to the dedicated audit log (logs/audit.log).
Uses the 'audit' logger configured in settings.py with the 'audit_file' handler.

Log format: AUDIT {timestamp} event=X | user=Y | plan=Z | amount=N | ...

All fields are pipe-delimited key=value pairs for easy grep/parsing:
    grep "event=subscription.cancelled" logs/audit.log
    grep "user=42" logs/audit.log
    grep "tokens.purchased" logs/audit.log | awk -F'|' '{print $5}'
"""

import logging
from typing import Optional, Dict, Any

audit_logger = logging.getLogger('audit')


def log_payment_event(
    event: str,
    user,
    *,
    subscription_id: str = None,
    payment_id: str = None,
    plan: str = None,
    amount: float = None,
    tokens: int = None,
    details: Dict[str, Any] = None,
    ip_address: str = None,
):
    """
    Log a payment event to the audit log.

    Args:
        event: Event name (e.g., 'subscription.created', 'tokens.purchased')
        user: Django User instance, user ID, or 'system' for automated events
        subscription_id: UUID string of the subscription
        payment_id: UUID string of the payment record
        plan: Plan display name
        amount: Payment amount (float)
        tokens: Token count affected
        details: Additional key-value pairs to log
        ip_address: Client IP address

    Events:
        subscription.created      New subscription activated
        subscription.upgraded     Plan upgraded (immediate)
        subscription.downgraded   Downgrade scheduled
        subscription.cancelled    Subscription cancelled
        subscription.expired      Subscription expired (task)
        subscription.suspended    Suspended after grace period (task)
        subscription.renewed      Auto-renewed (task)
        subscription.plan_changed Scheduled plan change applied (task)
        payment.verified          Razorpay payment verified
        payment.failed            Payment failed
        payment.refunded          Payment refunded
        tokens.purchased          Token package purchased
        tokens.auto_refill        Auto-refill triggered (task)
        tokens.expired            Referral tokens expired (task)
        webhook.received          Razorpay webhook processed
    """
    parts = [
        f"event={event}",
        f"user={user.id if hasattr(user, 'id') else user}",
        f"username={user.username if hasattr(user, 'username') else 'system'}",
    ]

    if subscription_id:
        parts.append(f"subscription={subscription_id}")
    if payment_id:
        parts.append(f"payment={payment_id}")
    if plan:
        parts.append(f"plan={plan}")
    if amount is not None:
        parts.append(f"amount={amount}")
    if tokens is not None:
        parts.append(f"tokens={tokens}")
    if ip_address:
        parts.append(f"ip={ip_address}")
    if details:
        for k, v in details.items():
            parts.append(f"{k}={v}")

    audit_logger.info(' | '.join(parts))


def get_client_ip(request) -> str:
    """Extract client IP from request, respecting X-Forwarded-For."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')