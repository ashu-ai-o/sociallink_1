from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from payments.models import UserSubscription, SubscriptionPlan
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Create free subscriptions for users without one'

    def handle(self, *args, **kwargs):
        free_plan = SubscriptionPlan.objects.get(name='free')
        users_without_sub = User.objects.filter(subscription__isnull=True)
        
        created_count = 0
        for user in users_without_sub:
            UserSubscription.objects.create(
                user=user,
                plan=free_plan,
                billing_cycle='monthly',
                status='active',
                is_trial=False,
                current_period_start=timezone.now(),
                current_period_end=timezone.now() + timedelta(days=30),
                auto_renew=False
            )
            created_count += 1
            
        self.stdout.write(self.style.SUCCESS(f'✅ Created {created_count} subscriptions'))