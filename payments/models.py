"""
Payment and Subscription Models for AI Platform
Token-based pricing with Razorpay integration
"""
import uuid
from decimal import Decimal
import logging
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from datetime import timedelta
from django.db.models import F

logger = logging.getLogger(__name__)


class SubscriptionPlan(models.Model):
    """
    Subscription plans matching the pricing screenshot
    """
    PLAN_TYPES = [
        ('free', 'Free'),    
        ('pro', 'Pro'),
        ('business', 'Business'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, choices=PLAN_TYPES, unique=True, default='free')
    display_name = models.CharField(max_length=100)
    description = models.TextField()


    # resets_monthly = models.BooleanField(
    #     default=True,
    #     help_text="If False, tokens are one-time allocation (for free tier)"
    # )
    
    # Pricing
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    annual_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], null=True, blank=True)
    
    # Token allocation
    # monthly_token_credits = models.IntegerField(default=100, help_text="Base monthly token credits")
    # daily_token_limit = models.IntegerField(default=150, help_text="Daily token usage limit")
    
    # Features (JSON field for flexibility)
    features = models.JSONField(default=dict, help_text="Plan-specific features")
    
    # Status
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Rollover configuration
    # rollover_enabled = models.BooleanField(default=False)
    # rollover_percentage = models.IntegerField(default=0, help_text="Percentage of monthly tokens that can roll over")

    plan_type = models.CharField(
        max_length=20,
        choices=[
            ('standard', 'Standard'),
            ('enterprise', 'Enterprise'),
            ('trial', 'Trial'),
        ],
        default='standard'
    )
    is_public = models.BooleanField(
        default=True,
        help_text="Show in public pricing page"
    )
    allow_self_service_changes = models.BooleanField(
        default=True,
        help_text="Allow users to change to/from this plan without approval"
    )
    minimum_commitment_days = models.IntegerField(
        default=0,
        help_text="Minimum days user must stay on this plan"
    )
    
    class Meta:
        db_table = 'subscription_plans'
        ordering = ['sort_order', 'monthly_price']
    
    def __str__(self):
        return f"{self.display_name} - ${self.monthly_price}/month"
    def get_annual_discount_percentage(self):
        """Calculate annual discount percentage"""
        if self.annual_price and self.monthly_price > 0:
            monthly_total = self.monthly_price * 12
            discount = ((monthly_total - self.annual_price) / monthly_total) * 100
            return round(discount, 1)
        return 0

class TaxRate(models.Model):
    """
    Dynamic tax rates based on country codes. 
    Prevents hardcoding tax rates in logic and enables updates via Django Admin.
    """
    country_code = models.CharField(
        max_length=10, 
        unique=True,
        help_text="2-letter ISO country code (e.g. 'IN', 'GB') or 'EU' / 'DEFAULT'."
    )
    tax_name = models.CharField(
        max_length=50,
        help_text="Display name for the tax (e.g. 'GST (18%)')"
    )
    rate = models.DecimalField(
        max_digits=5, 
        decimal_places=4,
        help_text="Tax rate as a decimal (e.g. 0.18 for 18%)"
    )
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tax_rates'
        ordering = ['country_code']
        
    def __str__(self):
        return f"{self.country_code} - {self.tax_name} ({self.rate * 100}%)"


class UserSubscription(models.Model):
    """
    User's active subscription with token tracking
    """
    BILLING_CYCLES = [
        ('monthly', 'Monthly'),
        ('annual', 'Annual'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
        ('trial', 'Trial'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    
    # Billing details
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLES, default='monthly')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')


    daily_reset_date = models.DateField(default=timezone.now)
    monthly_reset_date = models.DateField(default=timezone.now)
    
    is_blocked = models.BooleanField(default=False)
    block_reason = models.TextField(blank=True)
    blocked_at = models.DateTimeField(null=True, blank=True)
    
    usage_warning_sent = models.BooleanField(default=False)
    usage_critical_sent = models.BooleanField(default=False)
    

    
    # # Token tracking
    # tokens_remaining = models.IntegerField(default=0, help_text="Current token balance")
    # tokens_used_today = models.IntegerField(default=0, help_text="Tokens used today")
    # tokens_used_this_month = models.IntegerField(default=0, help_text="Tokens used this billing period")
    # total_tokens_used = models.IntegerField(default=0, help_text="Lifetime token usage")
    
    # # Additional purchased tokens
    # bonus_tokens = models.IntegerField(default=0, help_text="One-time purchased tokens")
    
    # # Rollover tokens from previous period
    # rollover_tokens = models.IntegerField(default=0, help_text="Unused tokens from previous period")
    
    # Dates
    start_date = models.DateTimeField(default=timezone.now)
    current_period_start = models.DateTimeField(default=timezone.now)
    current_period_end = models.DateTimeField()
    next_billing_date = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Razorpay integration
    razorpay_subscription_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    razorpay_customer_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Auto-renewal
    auto_renew = models.BooleanField(default=True)
    # auto_refill_enabled = models.BooleanField(default=False)
    # auto_refill_threshold = models.IntegerField(default=1000)
    # auto_refill_package = models.ForeignKey(
    #     'TokenPackage',
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     related_name='auto_refill_subscriptions'
    # )

    
    # Trial
    is_trial = models.BooleanField(default=False)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    scheduled_plan = models.ForeignKey(
        SubscriptionPlan, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='scheduled_subscriptions',
        help_text="Plan to switch to at next renewal"
    )
    scheduled_billing_cycle = models.CharField(
        max_length=20, 
        choices=BILLING_CYCLES, 
        null=True, 
        blank=True,
        help_text="Billing cycle for scheduled plan"
    )
    scheduled_change_reason = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Reason for scheduled change (downgrade/upgrade)"
    )
    
    # NEW FIELDS FOR PAYMENT STATUS TRACKING
    last_payment_status = models.CharField(
        max_length=20,
        choices=[
            ('success', 'Success'),
            ('failed', 'Failed'),
            ('pending', 'Pending'),
        ],
        default='success'
    )
    failed_payment_count = models.IntegerField(
        default=0,
        help_text="Number of consecutive failed payments"
    )

    
    # NEW FIELDS FOR SPECIAL PLAN TYPES
    plan_source = models.CharField(
        max_length=50,
        choices=[
            ('standard', 'Standard'),
            ('promo', 'Promotional'),
            ('coupon', 'Coupon'),
            ('enterprise', 'Enterprise'),
            ('referral', 'Referral'),
        ],
        default='standard'
    )
    promo_code_used = models.CharField(max_length=50, blank=True)
    commitment_end_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Minimum commitment period for special plans"
    )
    requires_admin_approval = models.BooleanField(
        default=False,
        help_text="Requires admin approval for plan changes"
    )

    # def check_and_refill(self):
    #     """Check if refill needed and trigger it"""
    #     if not self.auto_refill_enabled:
    #         return False
    #     if self.tokens_remaining <= self.auto_refill_threshold:
    #         if self.auto_refill_package:
    #             from .tasks import auto_purchase_tokens
    #             auto_purchase_tokens.delay(self.user.id, self.auto_refill_package.id)
    #             return True
    #     return False
    
    class Meta:
        db_table = 'user_subscriptions'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['razorpay_subscription_id']),
            models.Index(fields=['next_billing_date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.display_name} ({self.status})"
    
    def get_usage_percentage(self):
        """Returns monthly usage %"""
        if self.plan.monthly_token_credits == 0:
            return 100
        return (self.tokens_used_this_month / self.plan.monthly_token_credits) * 100
    
    def check_and_reset_periods(self):
        """Auto-reset daily/monthly counters"""
        today = timezone.now().date()
        
        if self.daily_reset_date < today:
            self.tokens_used_today = 0
            self.daily_reset_date = today + timedelta(days=1)
        
        if self.monthly_reset_date < today:
            self.tokens_used_this_month = 0
            self.monthly_reset_date = today + timedelta(days=30)
            self.usage_warning_sent = False
            self.usage_critical_sent = False
            
            # Unblock if was quota issue
            if self.is_blocked and 'quota' in self.block_reason.lower():
                self.is_blocked = False
                self.block_reason = ''
        
        self.save()

    
    # def reset_daily_usage(self):
    #     """Reset daily token usage counter"""
    #     self.tokens_used_today = 0
    #     self.save(update_fields=['tokens_used_today'])
    
    # def reset_monthly_usage(self):
    #     """Reset monthly token usage and allocate new tokens"""
    #     from django.utils import timezone
    #     from datetime import timedelta
        
    #     print(f"\n{'='*50}")
    #     print(f"🔄 Resetting monthly usage for {self.user.username}")
    #     print(f"{'='*50}")
        
    #     # Calculate rollover tokens
    #     if self.plan.rollover_enabled and self.tokens_remaining > 0:
    #         max_rollover = int(self.plan.monthly_token_credits * self.plan.rollover_percentage / 100)
    #         rollover = min(self.tokens_remaining, max_rollover)
    #         print(f"📦 Rollover: {rollover} tokens (max: {max_rollover})")
    #     else:
    #         rollover = 0
    #         print(f"📦 No rollover (disabled or no remaining tokens)")
        
    #     # Calculate new token allocation
    #     new_tokens = self.plan.monthly_token_credits + rollover
    #     print(f"💎 New allocation: {self.plan.monthly_token_credits} + {rollover} = {new_tokens}")
    #     print(f"🎁 Bonus tokens preserved: {self.bonus_tokens}")
        
    #     self.tokens_remaining = new_tokens
    #     self.rollover_tokens = rollover
    #     self.tokens_used_this_month = 0
    #     self.tokens_used_today = 0
        
    #     # Update billing period
    #     self.current_period_start = timezone.now()
    #     if self.billing_cycle == 'monthly':
    #         self.current_period_end = self.current_period_start + timedelta(days=30)
    #     else:
    #         self.current_period_end = self.current_period_start + timedelta(days=365)
        
    #     self.save()
    #     print(f"✅ Reset complete - {new_tokens} base tokens + {self.bonus_tokens} bonus")
    #     print(f"{'='*50}\n")


    # def can_use_tokens(self, token_count: int) -> tuple[bool, str]:
    #     """
    #     Check if user can use specified number of tokens
    #     Returns (can_use, reason)
    #     """
    #     # Check subscription status
    #     if self.status not in ['active', 'trial']:
    #         return False, f"Subscription is {self.status}"
        
    #     # Check if subscription expired
    #     if timezone.now() > self.current_period_end:
    #         return False, "Subscription period expired"
        
    #      # ✅ SKIP DAILY LIMIT for free tier (daily_token_limit = 0)
    #     if self.plan.daily_token_limit > 0:  # Only check if plan HAS daily limit
    #         if self.tokens_used_today + token_count > self.plan.daily_token_limit:
    #             return False, f"Daily token limit ({self.plan.daily_token_limit}) exceeded"
        
    #     # Check token balance
    #     if self.tokens_remaining < token_count:
    #         return False, "Insufficient tokens"
        
    #     return True, "OK"
    
    # def consume_tokens(self, token_count: int, description: str = "") -> bool:
    #     """
    #     Consume tokens and create usage record.
    #     Uses atomic F() expressions to prevent race conditions.
    #     Returns True if successful.
    #     """
    #     can_use, reason = self.can_use_tokens(token_count)

    #     if not can_use:
    #         # Create failed usage record
    #         TokenUsage.objects.create(
    #             user=self.user,
    #             subscription=self,
    #             tokens_used=0,
    #             tokens_requested=token_count,
    #             description=description,
    #             status='failed',
    #             failure_reason=reason
    #         )
    #         return False

    #     # ==========================================
    #     # 🔒 ATOMIC token deduction using F() expressions
    #     # This runs as a single SQL UPDATE — no read-modify-write race condition.
    #     #
    #     # Before (broken):
    #     #   self.tokens_remaining -= token_count  ← reads stale Python value
    #     #   self.save()                           ← overwrites concurrent writes
    #     #
    #     # After (safe):
    #     #   UPDATE SET tokens_remaining = tokens_remaining - N  ← atomic at DB level
    #     # ==========================================
    #     updated = UserSubscription.objects.filter(
    #         id=self.id,
    #         tokens_remaining__gte=token_count  # Double-check balance at DB level
    #     ).update(
    #         tokens_remaining=F('tokens_remaining') - token_count,
    #         tokens_used_today=F('tokens_used_today') + token_count,
    #         tokens_used_this_month=F('tokens_used_this_month') + token_count,
    #         total_tokens_used=F('total_tokens_used') + token_count,
    #     )

    #     if updated == 0:
    #         # Race condition caught: another request drained tokens between
    #         # can_use_tokens() check and the UPDATE. Log it and fail gracefully.
    #         TokenUsage.objects.create(
    #             user=self.user,
    #             subscription=self,
    #             tokens_used=0,
    #             tokens_requested=token_count,
    #             description=description,
    #             status='failed',
    #             failure_reason='Insufficient tokens (race condition prevented)'
    #         )
    #         return False

    #     # Refresh Python object to reflect the DB-level changes
    #     self.refresh_from_db()

    #     # Create success usage record
    #     TokenUsage.objects.create(
    #         user=self.user,
    #         subscription=self,
    #         tokens_used=token_count,
    #         tokens_requested=token_count,
    #         description=description,
    #         status='success'
    #     )

    #     return True

    
    # def add_bonus_tokens(self, token_count: int):
    #     """Add bonus/purchased tokens"""
    #     self.tokens_remaining += token_count
    #     self.bonus_tokens += token_count
    #     self.save(update_fields=['tokens_remaining', 'bonus_tokens'])

    def can_change_plan(self, new_plan, new_billing_cycle='monthly'):
        """
        Check if user can change to new plan
        Returns: (can_change: bool, reason: str, is_upgrade: bool)
        """
        from django.utils import timezone
        from decimal import Decimal
        
        # Check if subscription is active
        if self.status not in ['active', 'trial']:
            return False, f"Cannot change plan while subscription is {self.status}", False
        
        # Check for failed payments
        if self.last_payment_status == 'failed' and self.failed_payment_count > 0:
            return False, "Please resolve pending payment issues before changing plans", False
        
        # Check for commitment period
        if self.commitment_end_date and self.commitment_end_date > timezone.now():
            days_remaining = (self.commitment_end_date - timezone.now()).days
            return False, f"You have a commitment period until {self.commitment_end_date.date()}. {days_remaining} days remaining.", False
        
        # Check if requires admin approval
        if self.requires_admin_approval or self.plan_source in ['enterprise', 'promo']:
            return False, "Plan changes require admin approval. Please contact support.", False
        
        # Calculate absolute contract values for upgrade/downgrade logic
        current_price = (
            self.plan.annual_price 
            if self.billing_cycle == 'annual' 
            else self.plan.monthly_price
        )
        
        new_price = (
            new_plan.annual_price 
            if new_billing_cycle == 'annual' 
            else new_plan.monthly_price
        )
        
        is_upgrade = new_price > current_price
        
        # Check for mid-cycle downgrade
        if not is_upgrade:
            days_until_renewal = (self.current_period_end - timezone.now()).days
            
            # Allow downgrade only if within 1 day of renewal
            if days_until_renewal > 1:
                return False, f"Downgrades are only allowed at renewal time. Your next renewal is in {days_until_renewal} days.", False
        
        return True, "", is_upgrade
    
    def schedule_plan_change(self, new_plan, new_billing_cycle, reason=""):
        """Schedule a plan change for next renewal"""
        self.scheduled_plan = new_plan
        self.scheduled_billing_cycle = new_billing_cycle
        self.scheduled_change_reason = reason
        self.save(update_fields=['scheduled_plan', 'scheduled_billing_cycle', 'scheduled_change_reason'])
    
    def apply_scheduled_change(self):
        """Apply scheduled plan change (called at renewal)"""
        if self.scheduled_plan:
            old_plan = self.plan
            self.plan = self.scheduled_plan
            self.billing_cycle = self.scheduled_billing_cycle
            
            self.scheduled_plan = None
            self.scheduled_billing_cycle = None
            self.scheduled_change_reason = ""
            self.save()
            return True, f"Plan changed from {old_plan.display_name} to {self.plan.display_name}"
        return False, "No scheduled change"
    
    def check_token_loss(self, new_plan):
        """Check if user will lose tokens on plan change"""
        # Tokens are deprecated; feature uses limit tracking in DB instead
        return False, 0


# class TokenUsage(models.Model):
#     """
#     Detailed token usage tracking for analytics and billing
#     """
#     STATUS_CHOICES = [
#         ('success', 'Success'),
#         ('failed', 'Failed'),
#         ('refunded', 'Refunded'),
#     ]
    
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_token_usage')
#     subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE, related_name='usage_records')
    
#     # Token details
#     tokens_used = models.IntegerField(validators=[MinValueValidator(0)])
#     tokens_requested = models.IntegerField(validators=[MinValueValidator(0)])
    
#     # Context
#     description = models.CharField(max_length=255, blank=True)
#     project_id = models.UUIDField(null=True, blank=True, help_text="Associated project")
#     feature = models.CharField(max_length=100, blank=True, help_text="Feature that consumed tokens")
    
#     # AI model details
#     ai_model_used = models.CharField(max_length=100, blank=True)
#     prompt_tokens = models.IntegerField(default=0)
#     completion_tokens = models.IntegerField(default=0)
    
#     # Status
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='success')
#     failure_reason = models.TextField(blank=True)
    
#     # Metadata
#     metadata = models.JSONField(default=dict, help_text="Additional usage metadata")
    
#     created_at = models.DateTimeField(auto_now_add=True)
    
#     class Meta:
#         db_table = 'token_usage'
#         ordering = ['-created_at']
#         indexes = [
#             models.Index(fields=['user', '-created_at']),
#             models.Index(fields=['subscription', '-created_at']),
#             models.Index(fields=['status', '-created_at']),
#             models.Index(fields=['created_at']),
#         ]
    
#     def __str__(self):
#         return f"{self.user.username} - {self.tokens_used} tokens - {self.created_at}"


class Payment(models.Model):
    """
    Payment transaction records
    """
    PAYMENT_TYPES = [
        ('subscription', 'Subscription'),
        ('token_purchase', 'Token Purchase'),
        ('upgrade', 'Plan Upgrade'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    CURRENCY_CHOICES = [
        ('INR', 'Indian Rupee'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    subscription = models.ForeignKey(UserSubscription, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Payment details
    payment_type = models.CharField(max_length=50, choices=PAYMENT_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='INR')
    
    # Razorpay details
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    failure_reason = models.TextField(blank=True)
    
    # Token purchase details (if applicable)
    tokens_purchased = models.IntegerField(default=0, help_text="Tokens purchased in this transaction")
    
    # Billing details
    billing_address = models.JSONField(default=dict, blank=True)
    invoice_number = models.CharField(max_length=50, blank=True, unique=True)
    
    # Metadata
    metadata = models.JSONField(default=dict)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['razorpay_order_id']),
            models.Index(fields=['razorpay_payment_id']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.amount} {self.currency} - {self.status}"
    
    def save(self, *args, **kwargs):
        """Override save to auto-generate invoice number"""
        # First save to ensure we have an ID
        is_new = self._state.adding
        if is_new:
            # Temporarily remove unique constraint check
            self.invoice_number = f"TEMP_{uuid.uuid4().hex[:12]}"
        
        super().save(*args, **kwargs)
        
        # Generate final invoice number after ID is created
        if is_new:
            self._generate_invoice_number()
    
    def _generate_invoice_number(self):
        """Generate unique invoice number with guaranteed uniqueness"""
        if not self.id:
            raise ValueError("Cannot generate invoice number before object is saved")
        
        prefix = "INV"
        # Include microseconds for better uniqueness
        timestamp = timezone.now().strftime("%Y%m%d%H%M%S%f")
        # Use UUID.hex to get the hex string without dashes
        unique_id = self.id.hex[-12:].upper()
        
        invoice_number = f"{prefix}-{timestamp}-{unique_id}"
        
        # Use update to avoid recursion and save signal triggers
        Payment.objects.filter(id=self.id).update(invoice_number=invoice_number)
        
        # Update the instance's attribute to reflect the change
        self.invoice_number = invoice_number
        
        return invoice_number


# class TokenPackage(models.Model):
#     """
#     One-time token purchase packages
#     """
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     name = models.CharField(max_length=100)
#     description = models.TextField()
    
#     # Tokens and pricing
#     token_count = models.IntegerField(validators=[MinValueValidator(1)])
#     price_inr = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
#     price_usd = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
#     # Bonus
#     bonus_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Bonus tokens %")
    
#     # Status
#     is_active = models.BooleanField(default=True)
#     is_featured = models.BooleanField(default=False)
#     sort_order = models.IntegerField(default=0)
    
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     class Meta:
#         db_table = 'token_packages'
#         ordering = ['sort_order', 'token_count']
    
#     def __str__(self):
#         return f"{self.name} - {self.token_count} tokens"
    
#     def get_total_tokens(self):
#         """Calculate total tokens including bonus"""
#         bonus = int(self.token_count * float(self.bonus_percentage) / 100)
#         return self.token_count + bonus
    
#     def get_price_for_currency(self, currency: str) -> Decimal:
#         """Get price for specified currency"""
#         if currency == 'INR':
#             return self.price_inr
#         elif currency == 'USD':
#             return self.price_usd
#         else:
#             # Convert from USD for other currencies
#             return self.price_usd


# WebhookLog is defined in analytics.models — DO NOT duplicate here
# class WebhookLog(models.Model):
#     ... (see analytics/models.py)


# payments/models.py

class PaymentMethod(models.Model):
    """Saved payment methods for users"""
    PAYMENT_METHOD_TYPES = [
        ('card', 'Credit/Debit Card'),
        ('netbanking', 'Net Banking'),
        ('upi', 'UPI'),
        ('wallet', 'Wallet'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_methods')
    
    # Razorpay details
    razorpay_payment_id = models.CharField(max_length=100, unique=True, help_text="Razorpay Payment ID",null=True, blank=True)
    
    # Method details
    method_type = models.CharField(max_length=20, choices=PAYMENT_METHOD_TYPES)
    
    # Card-specific fields
    last4 = models.CharField(max_length=4, blank=True, help_text="Last 4 digits of card")
    card_network = models.CharField(max_length=50, blank=True, help_text="Visa, Mastercard, etc.")
    card_issuer = models.CharField(max_length=100, blank=True, help_text="Bank name")
    card_type = models.CharField(max_length=20, blank=True, help_text="credit/debit")
    
    # UPI-specific fields
    upi_vpa = models.CharField(max_length=100, blank=True, help_text="UPI VPA")
    
    # NetBanking-specific fields
    bank_name = models.CharField(max_length=100, blank=True, help_text="Bank name for netbanking")
    
    # Wallet-specific fields
    wallet_name = models.CharField(max_length=100, blank=True, help_text="Wallet provider name")
    
    # Email associated with payment
    email = models.EmailField(blank=True)
    contact = models.CharField(max_length=20, blank=True)
    
    # Status
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'payment_methods'
        ordering = ['-is_default', '-last_used_at']
    
    def __str__(self):
        if self.method_type == 'card':
            return f"{self.user.username} - {self.card_network} {self.last4}"
        elif self.method_type == 'upi':
            return f"{self.user.username} - UPI {self.upi_vpa}"
        elif self.method_type == 'netbanking':
            return f"{self.user.username} - {self.bank_name}"
        elif self.method_type == 'wallet':
            return f"{self.user.username} - {self.wallet_name}"
        return f"{self.user.username} - {self.method_type}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default payment method per user
        if self.is_default:
            PaymentMethod.objects.filter(
                user=self.user,
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)
    
    def get_display_name(self):
        """Get user-friendly display name"""
        if self.method_type == 'card':
            return f"{self.card_network} ending in {self.last4}"
        elif self.method_type == 'upi':
            return f"UPI - {self.upi_vpa}"
        elif self.method_type == 'netbanking':
            return f"{self.bank_name} NetBanking"
        elif self.method_type == 'wallet':
            return f"{self.wallet_name} Wallet"
        return self.method_type.upper()

# payments/models.py

class ReferralCode(models.Model):
    """User referral codes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referral_code')
    code = models.CharField(max_length=20, unique=True)
    
    # Rewards
    referrer_bonus_tokens = models.IntegerField(default=5000)
    referee_bonus_tokens = models.IntegerField(default=2000)
    
    # Stats
    total_referrals = models.IntegerField(default=0)
    total_earned_tokens = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'referral_codes'
    
    def __str__(self):
        return f"{self.user.username} - {self.code}"
    
    @staticmethod
    def generate_code(username):
        """Generate unique referral code"""
        import random
        import string
        base = username[:4].upper()
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"{base}{random_suffix}"


class Referral(models.Model):
    """Track referrals"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    referrer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referrals_made')
    referee = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referred_by')
    referral_code = models.ForeignKey(ReferralCode, on_delete=models.CASCADE)
    
    # Rewards
    referrer_tokens_awarded = models.IntegerField(default=0)
    referee_tokens_awarded = models.IntegerField(default=0)
    rewards_processed = models.BooleanField(default=False)
    
    # Subscription requirement
    referee_subscribed = models.BooleanField(default=False)
    subscription_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'referrals'
        
    def process_rewards(self):
        """Award tokens to both parties"""
        if self.rewards_processed:
            return False
        
        try:
            # Award tokens to referee
            referee_subscription = UserSubscription.objects.get(user=self.referee)
            referee_subscription.bonus_tokens += self.referral_code.referee_bonus_tokens
            referee_subscription.save()
            self.referee_tokens_awarded = self.referral_code.referee_bonus_tokens
            
            # Award tokens to referrer
            referrer_subscription = UserSubscription.objects.get(user=self.referrer)
            referrer_subscription.bonus_tokens += self.referral_code.referrer_bonus_tokens
            referrer_subscription.save()
            self.referrer_tokens_awarded = self.referral_code.referrer_bonus_tokens
            
            # Update stats
            self.referral_code.total_referrals += 1
            self.referral_code.total_earned_tokens += self.referral_code.referrer_bonus_tokens
            self.referral_code.save()
            
            self.rewards_processed = True
            self.save()
            
            return True
        except Exception as e:
            logger.error(f"Error processing referral rewards: {e}")
            return False


"""
Additional Models for Email System
"""

class EmailLog(models.Model):
    """
    Log all email communications for tracking and debugging
    """
    EMAIL_TYPES = [
        ('payment_receipt', 'Payment Receipt'),
        ('payment_failure', 'Payment Failure'),
        ('subscription_reminder', 'Subscription Reminder'),
        ('refund_notification', 'Refund Notification'),
        ('trial_expiring', 'Trial Expiring Soon'),
        ('trial_expired', 'Trial Expired'),
        ('subscription_expired', 'Subscription Expired'),
        ('subscription_suspended', 'Subscription Suspended'),
        ('subscription_renewed', 'Subscription Renewed'),
        ('plan_change_applied', 'Plan Change Applied'),
        ('low_token_balance', 'Low Token Balance'),
    ]
    
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('failed_final', 'Failed Final'),
        ('bounced', 'Bounced'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='email_logs'
    )
    payment = models.ForeignKey(
        'Payment', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='email_logs'
    )
    
    # Email details
    email_type = models.CharField(max_length=50, choices=EMAIL_TYPES)
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    
    # Tracking
    sent_at = models.DateTimeField(auto_now_add=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'email_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['email_type', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.email_type} - {self.recipient} - {self.status}"
    
    def mark_as_opened(self):
        """Mark email as opened"""
        if not self.opened_at:
            self.opened_at = timezone.now()
            self.status = 'opened'
            self.save(update_fields=['opened_at', 'status'])
    
    def mark_as_clicked(self):
        """Mark email links as clicked"""
        if not self.clicked_at:
            self.clicked_at = timezone.now()
            self.status = 'clicked'
            self.save(update_fields=['clicked_at', 'status'])
    
    @property
    def open_rate(self):
        """Calculate if email was opened"""
        return self.opened_at is not None
    
    @property
    def click_rate(self):
        """Calculate if email links were clicked"""
        return self.clicked_at is not None


# ══════════════════════════════════════════════════════════
# PROXY MODEL — Only exists to mount the Celery Task Runner
# in Django Admin. Has no DB table of its own.
# ══════════════════════════════════════════════════════════

class CeleryTaskRunner(Payment):
    """
    Proxy model used exclusively as an admin mount point for 
    the Celery Task Runner dashboard.
    
    No migration creates a new table — proxy=True means it
    reuses the Payment table but gets its own admin entry.
    """
    class Meta:
        proxy = True
        verbose_name = 'Celery Task Runner'
        verbose_name_plural = '⚙️ Celery Task Runner (Payments)'
        app_label = 'payments'