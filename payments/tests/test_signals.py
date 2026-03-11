from django.test import TestCase
from django.contrib.auth import get_user_model
from payments.models import UserSubscription, SubscriptionPlan
from django.utils import timezone

User = get_user_model()

class SubscriptionSignalTest(TestCase):
    def setUp(self):
        # Create the 'free' plan which the signal expects
        self.free_plan = SubscriptionPlan.objects.create(
            name='free',
            display_name='Free Plan',
            description='Free tier plan',
            monthly_price=0,
            is_active=True
        )

    def test_user_creation_creates_free_subscription(self):
        """Verify that creating a new User triggers the signal and creates a UserSubscription"""
        user = User.objects.create_user(
            username='testuser',
            email='testuser@gmail.com',
            password='testpassword123'
        )
        
        # Check if subscription was created
        subscription = UserSubscription.objects.filter(user=user).first()
        self.assertIsNotNone(subscription)
        self.assertEqual(subscription.plan, self.free_plan)
        self.assertEqual(subscription.status, 'active')
        
    def test_duplicate_user_creation_handled_by_service(self):
        """Ensure that the service layer handles existing subscriptions gracefully (idempotency)"""
        user = User.objects.create_user(
            username='testuser2',
            email='testuser2@gmail.com',
            password='testpassword123'
        )
        
        # Manually call service to see if it creates a second one (it shouldn't)
        from payments.services import SubscriptionService
        SubscriptionService.create_initial_free_subscription(user)
        
        self.assertEqual(UserSubscription.objects.filter(user=user).count(), 1)
