"""
Management Command to Initialize Subscription Plans
Run: python manage.py init_subscription_plans
"""
from django.core.management.base import BaseCommand
from payments.models import SubscriptionPlan
from decimal import Decimal


class Command(BaseCommand):
    help = 'Initialize subscription plans and token packages based on pricing screenshot'
    
    def handle(self, *args, **options):
        self.stdout.write('Initializing subscription plans...')


        # --------------------------------------
        # Create Trial Plan (Newly Added)
        # --------------------------------------
        trial_plan, created = SubscriptionPlan.objects.update_or_create(
            name='free',
            defaults={
                'display_name': 'Free ',
                'description': 'Try all essential features with limited credits.',
                'monthly_price': Decimal('0.00'),
                'annual_price': Decimal('0.00'),
                'monthly_token_credits': 100000,  # You can adjust
                'daily_token_limit': 0,
                'is_active': True,
                'sort_order': 0,   # appears before Pro plan
                'features': {"one_time_tokens": True,
                              "no_reset": True,
                              "must_upgrade": True
                              }
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created Trial plan'))
        else:
            self.stdout.write(self.style.WARNING(f'Updated Trial plan'))
        


        # Create Pro Plan
        pro_plan, created = SubscriptionPlan.objects.update_or_create(
            name='pro',
            defaults={
                'display_name': 'Pro',
                'description': 'Designed for fast-moving teams building together in real time.',
                'monthly_price': Decimal('25.00'),
                'annual_price': Decimal('240.00'),  # 20% discount
                'monthly_token_credits': 100,
                'daily_token_limit': 150,
                'is_active': True,
                'sort_order': 1,
                'features': {
                    '100_monthly_credits': True,
                    'daily_credits': 5,
                    'daily_limit': 150,
                    'usage_based_cloud_ai': True,
                    'credit_rollovers': True,
                    'custom_domains': True,
                    'remove_lovable_badge': True,
                }
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created Pro plan'))
        else:
            self.stdout.write(self.style.WARNING(f'Updated Pro plan'))
        
        # Create Business Plan
        business_plan, created = SubscriptionPlan.objects.update_or_create(
            name='business',
            defaults={
                'display_name': 'Business',
                'description': 'Advanced controls and power features for growing departments',
                'monthly_price': Decimal('50.00'),
                'annual_price': Decimal('480.00'),  # 20% discount
                'monthly_token_credits': 100,
                'daily_token_limit': 150,
                'is_active': True,
                'sort_order': 2,
                'features': {
                    '100_monthly_credits': True,
                    'internal_publish': True,
                    'sso': True,
                    'personal_projects': True,
                    'opt_out_data_training': True,
                    'design_templates': True,
                }
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created Business plan'))
        else:
            self.stdout.write(self.style.WARNING(f'Updated Business plan'))
        
        
        
        self.stdout.write('\nInitializing token packages...')
        
        # Token packages for one-time purchases
        token_packages = [
            {
                'name': 'Starter Pack',
                'description': 'Perfect for small projects',
                'token_count': 100,
                'price_inr': Decimal('500.00'),
                'price_usd': Decimal('10.00'),
                'bonus_percentage': Decimal('0.00'),
                'is_featured': False,
                'sort_order': 1,
            },
            {
                'name': 'Professional Pack',
                'description': 'Most popular choice',
                'token_count': 500,
                'price_inr': Decimal('2000.00'),
                'price_usd': Decimal('40.00'),
                'bonus_percentage': Decimal('10.00'),  # 10% bonus
                'is_featured': True,
                'sort_order': 2,
            },
            {
                'name': 'Business Pack',
                'description': 'Best value for serious users',
                'token_count': 1000,
                'price_inr': Decimal('3500.00'),
                'price_usd': Decimal('70.00'),
                'bonus_percentage': Decimal('20.00'),  # 20% bonus
                'is_featured': False,
                'sort_order': 3,
            },
            {
                'name': 'Enterprise Pack',
                'description': 'Maximum tokens for large teams',
                'token_count': 5000,
                'price_inr': Decimal('15000.00'),
                'price_usd': Decimal('300.00'),
                'bonus_percentage': Decimal('30.00'),  # 30% bonus
                'is_featured': False,
                'sort_order': 4,
            },
        ]
        
        for package_data in token_packages:
            name = package_data.pop('name')
            package, created = TokenPackage.objects.update_or_create(
                name=name,
                defaults=package_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created token package: {name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Updated token package: {name}'))
        
        self.stdout.write(self.style.SUCCESS('\n✓ All subscription plans and token packages initialized successfully!'))