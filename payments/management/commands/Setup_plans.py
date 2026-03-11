"""
Management Command to Setup Subscription Plans
Run: python manage.py setup_plans
"""
from django.core.management.base import BaseCommand
from payments.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Create default subscription plans (Free, Pro, Business, Enterprise)'

    def handle(self, *args, **options):
        self.stdout.write('Setting up subscription plans...\n')

        plans_data = [
            {
                'name': 'free',
                'display_name': 'Free',
                'description': 'Get started with basic automations',
                'monthly_price': 0,
                'annual_price': 0,
                'is_active': True,
                'sort_order': 0,
                'plan_type': 'standard',
                'is_public': True,
                'features': {
                    'automations': 3,
                    'dms_per_month': 500,
                    'advanced_analytics': False,
                    'remove_badge': False,
                    'priority_support': False,
                }
            },
            {
                'name': 'pro',
                'display_name': 'Pro',
                'description': 'For professionals who need more power',
                'monthly_price': 10,
                'annual_price': 100,  # 2 months free
                'is_active': True,
                'sort_order': 1,
                'plan_type': 'standard',
                'is_public': True,
                'features': {
                    'automations': 10,
                    'dms_per_month': 5000,
                    'advanced_analytics': True,
                    'remove_badge': True,
                    'priority_support': True,
                }
            },
            {
                'name': 'business',
                'display_name': 'Business',
                'description': 'For teams and growing businesses',
                'monthly_price': 20,
                'annual_price': 200,  # 2 months free
                'is_active': True,
                'sort_order': 2,
                'plan_type': 'standard',
                'is_public': True,
                'features': {
                    'automations': 50,
                    'dms_per_month': -1, # unlimited
                    'advanced_analytics': True,
                    'remove_badge': True,
                    'priority_support': True,
                }
            },
            
        ]

        created_count = 0
        updated_count = 0

        for plan_data in plans_data:
            plan, created = SubscriptionPlan.objects.update_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created: {plan.display_name} plan')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'🔄 Updated: {plan.display_name} plan')
                )

        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Setup complete! Created: {created_count}, Updated: {updated_count}'
            )
        )
        
        # Show all plans
        self.stdout.write('\n📋 Current Plans:')
        for plan in SubscriptionPlan.objects.all().order_by('sort_order'):
            auth_feat = plan.features.get('automations', 0)
            dm_feat = plan.features.get('dms_per_month', 0)
            self.stdout.write(
                f'   - {plan.display_name}: ₹{plan.monthly_price}/mo, '
                f'{auth_feat} automations, {dm_feat} DMs/mo'
            )