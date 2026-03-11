"""
Django Signals for Payment Module
Handles automatic subscription lifecycle events
"""
from asyncio.log import logger
from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings  # ✅ ADD THIS
from django.utils import timezone
from datetime import timedelta
from .models import UserSubscription, SubscriptionPlan


# ✅ Use get_user_model() or settings.AUTH_USER_MODEL
from django.contrib.auth import get_user_model
User = get_user_model()


@receiver(post_save, sender=User)
def create_trial_subscription(sender, instance, created, **kwargs):
    """Auto-create FREE subscription on new user signup"""
    if created:
        from .services import SubscriptionService
        SubscriptionService.create_initial_free_subscription(instance)