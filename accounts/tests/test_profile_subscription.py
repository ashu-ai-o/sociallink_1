from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from payments.models import UserSubscription, SubscriptionPlan

User = get_user_model()

# Use in-memory cache during tests so Redis isn't required
TEST_CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

@override_settings(CACHES=TEST_CACHES)
class ProfileSubscriptionAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create the free plan BEFORE creating the user so the signal can find it
        self.free_plan, _ = SubscriptionPlan.objects.get_or_create(
            name='free',
            defaults={
                'display_name': 'Free Plan',
                'description': 'Free tier plan',
                'monthly_price': 0,
            }
        )

        self.user = User.objects.create_user(
            username='apiuser',
            email='apiuser@yahoo.com',
            password='apipassword123',
            is_email_verified=True
        )
        self.client.force_authenticate(user=self.user)

    def test_profile_includes_subscription_data(self):
        """Verify that the /api/auth/profile/ endpoint returns subscription details"""
        # Verify the signal created the subscription
        sub_exists = UserSubscription.objects.filter(user=self.user).exists()
        self.assertTrue(sub_exists, "Signal should have created a subscription on user creation")
        
        # Ensure it exists for safety
        if not sub_exists:
            from django.utils import timezone
            from datetime import timedelta
            UserSubscription.objects.create(
                user=self.user,
                plan=self.free_plan,
                status='active',
                current_period_end=timezone.now() + timedelta(days=30),
            )

        response = self.client.get('/api/auth/profile/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('subscription', data)
        
        # Debug: if subscription is None, print the full response for diagnosis
        if data['subscription'] is None:
            # Check if the subscription exists in DB
            sub = UserSubscription.objects.filter(user=self.user).first()
            self.fail(
                f"subscription field is None in response. "
                f"DB subscription exists: {sub is not None}. "
                f"Sub details: plan={sub.plan.display_name if sub else 'N/A'}, status={sub.status if sub else 'N/A'}. "
                f"Full response keys: {list(data.keys())}"
            )
        
        self.assertEqual(data['subscription']['plan_name'], 'Free Plan')
