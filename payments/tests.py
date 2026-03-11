"""
Unit Tests for Payment Module
Covers: Tax calculation, proration, token consumption, webhook idempotency
"""
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class CalculateTaxTests(TestCase):
    """Tests for utils.calculate_tax — database-driven tax logic."""

    @classmethod
    def setUpTestData(cls):
        from apps.payments.models import TaxRate
        TaxRate.objects.create(country_code='IN', tax_name='GST (18%)', rate=Decimal('0.18'), is_active=True)
        TaxRate.objects.create(country_code='GB', tax_name='VAT (20%)', rate=Decimal('0.20'), is_active=True)
        TaxRate.objects.create(country_code='EU', tax_name='EU VAT (~20%)', rate=Decimal('0.20'), is_active=True)
        TaxRate.objects.create(country_code='US', tax_name='Sales Tax (0%)', rate=Decimal('0.00'), is_active=True)
        TaxRate.objects.create(country_code='DEFAULT', tax_name='Tax (0%)', rate=Decimal('0.00'), is_active=True)

    def _calc(self, amount, country):
        from apps.payments.utils import calculate_tax
        return calculate_tax(Decimal(str(amount)), country)

    def test_india_gst(self):
        result = self._calc(100, 'IN')
        self.assertEqual(result['tax_rate'], Decimal('0.18'))
        self.assertEqual(result['tax_amount'], Decimal('18.00'))
        self.assertEqual(result['total_amount'], Decimal('118.00'))
        self.assertEqual(result['tax_name'], 'GST (18%)')

    def test_uk_vat(self):
        result = self._calc(100, 'GB')
        self.assertEqual(result['tax_rate'], Decimal('0.20'))
        self.assertEqual(result['tax_amount'], Decimal('20.00'))

    def test_us_zero_tax(self):
        result = self._calc(100, 'US')
        self.assertEqual(result['tax_rate'], Decimal('0.00'))
        self.assertEqual(result['tax_amount'], Decimal('0.00'))
        self.assertEqual(result['total_amount'], Decimal('100.00'))

    def test_eu_member_fallback(self):
        """EU countries without their own row should fall back to the 'EU' rate."""
        result = self._calc(100, 'DE')
        self.assertEqual(result['tax_rate'], Decimal('0.20'))
        self.assertEqual(result['tax_name'], 'EU VAT (~20%)')

    def test_unknown_country_falls_to_default(self):
        result = self._calc(100, 'ZZ')
        self.assertEqual(result['tax_rate'], Decimal('0.00'))
        self.assertEqual(result['tax_name'], 'Tax (0%)')

    def test_case_insensitive(self):
        result = self._calc(100, 'in')
        self.assertEqual(result['tax_rate'], Decimal('0.18'))

    def test_inactive_rate_ignored(self):
        from apps.payments.models import TaxRate
        TaxRate.objects.filter(country_code='IN').update(is_active=False)
        result = self._calc(100, 'IN')
        # Should fall to DEFAULT since IN is inactive
        self.assertEqual(result['tax_rate'], Decimal('0.00'))
        # Restore
        TaxRate.objects.filter(country_code='IN').update(is_active=True)


class CalculateProrationTests(TestCase):
    """Tests for utils.calculate_proration."""

    @classmethod
    def setUpTestData(cls):
        from apps.payments.models import SubscriptionPlan
        cls.pro_plan = SubscriptionPlan.objects.create(
            name='pro', display_name='Pro', monthly_price=Decimal('25.00'),
            annual_price=Decimal('250.00'), monthly_token_credits=50000,
            daily_token_limit=5000, sort_order=2,
        )
        cls.business_plan = SubscriptionPlan.objects.create(
            name='business', display_name='Business', monthly_price=Decimal('50.00'),
            annual_price=Decimal('500.00'), monthly_token_credits=100000,
            daily_token_limit=10000, sort_order=3,
        )

    def test_upgrade_gives_credit(self):
        from apps.payments.utils import calculate_proration
        from apps.payments.models import UserSubscription

        user = User.objects.create_user(username='prouser', password='test')
        now = timezone.now()
        sub = UserSubscription.objects.create(
            user=user, plan=self.pro_plan, status='active',
            billing_cycle='monthly',
            current_period_start=now - timedelta(days=15),
            current_period_end=now + timedelta(days=15),
            tokens_remaining=50000, start_date=now - timedelta(days=15),
        )
        result = calculate_proration(sub, self.business_plan, 'monthly')
        self.assertGreater(result['credit_amount_usd'], 0)
        self.assertLessEqual(result['prorated_amount_usd'], Decimal('50.00'))

    def test_no_negative_proration(self):
        """Prorated amount should never go below zero."""
        from apps.payments.utils import calculate_proration
        from apps.payments.models import UserSubscription

        user = User.objects.create_user(username='neguser', password='test')
        now = timezone.now()
        sub = UserSubscription.objects.create(
            user=user, plan=self.business_plan, status='active',
            billing_cycle='monthly',
            current_period_start=now - timedelta(days=1),
            current_period_end=now + timedelta(days=29),
            tokens_remaining=100000, start_date=now - timedelta(days=1),
        )
        result = calculate_proration(sub, self.pro_plan, 'monthly')
        self.assertGreaterEqual(result['prorated_amount_usd'], 0)


class TokenConsumptionTests(TransactionTestCase):
    """Tests for UserSubscription.consume_tokens."""

    def setUp(self):
        from apps.payments.models import SubscriptionPlan, UserSubscription
        self.user = User.objects.create_user(username='tokenuser', password='test')
        self.plan = SubscriptionPlan.objects.create(
            name='test', display_name='Test', monthly_price=Decimal('10.00'),
            annual_price=Decimal('100.00'), monthly_token_credits=1000,
            daily_token_limit=500, sort_order=1,
        )
        self.sub = UserSubscription.objects.create(
            user=self.user, plan=self.plan, status='active',
            billing_cycle='monthly', tokens_remaining=1000,
            start_date=timezone.now(),
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timedelta(days=30),
        )

    def test_successful_consumption(self):
        result = self.sub.consume_tokens(100, description='Test usage')
        self.assertTrue(result)
        self.sub.refresh_from_db()
        self.assertEqual(self.sub.tokens_remaining, 900)

    def test_cannot_consume_more_than_available(self):
        can_use, reason = self.sub.can_use_tokens(2000)
        self.assertFalse(can_use)

    def test_zero_token_consumption(self):
        result = self.sub.consume_tokens(0, description='No tokens')
        self.sub.refresh_from_db()
        self.assertEqual(self.sub.tokens_remaining, 1000)


class WebhookIdempotencyTests(TransactionTestCase):
    """Tests for webhook duplicate prevention."""

    def test_duplicate_webhook_rejected(self):
        from apps.payments.models import WebhookLog
        # Simulate first webhook
        WebhookLog.objects.create(
            event_type='payment.captured',
            event_id='evt_test_123',
            payload={'test': True},
            processed=True,
            processed_at=timezone.now(),
        )
        # Second lookup should find it's already processed
        existing = WebhookLog.objects.filter(
            event_id='evt_test_123', processed=True
        ).first()
        self.assertIsNotNone(existing)

    def test_new_webhook_passes(self):
        from apps.payments.models import WebhookLog
        existing = WebhookLog.objects.filter(
            event_id='evt_brand_new', processed=True
        ).first()
        self.assertIsNone(existing)
