"""
Django Admin Configuration for Payment Models
WITH TIMEZONE FIXES
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.utils.safestring import mark_safe
from django.utils.timezone import localtime
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import render
from .models import (
    PaymentMethod, SubscriptionPlan, UserSubscription, Payment,
    # TokenPackage, TokenUsage,
    CeleryTaskRunner, TaxRate
)
# WebhookLog admin is in analytics/admin.py




class PaymentTaskRunnerAdminBase(admin.ModelAdmin):
    """
    Custom admin that renders a dashboard of all payment Celery tasks
    with Run Now buttons. No model data is displayed.
    """

    # ── Complete list of every payment task in your project ──────────────────
    PAYMENT_TASKS = [

        # ── Subscription Lifecycle ──────────────────────────────────────────
        {
            'id': 'check_expired_subscriptions',
            'label': 'Check Expired Subscriptions',
            'description': 'Marks subscriptions past current_period_end as expired, zeros tokens. Runs every 12h.',
            'task': 'apps.payments.tasks.check_expired_subscriptions',
            'group': '📦 Subscription Lifecycle',
            'danger': False,
        },
        {
            'id': 'check_trial_expirations',
            'label': 'Check Trial Expirations',
            'description': 'Finds expired trial subscriptions, sets status=expired, zeros tokens. Runs every 12h.',
            'task': 'apps.payments.tasks.check_trial_expirations',
            'group': '📦 Subscription Lifecycle',
            'danger': False,
        },
        {
            'id': 'process_subscription_renewals',
            'label': 'Process Subscription Renewals',
            'description': 'Processes auto-renew subscriptions due in next 24h. Runs every 6h.',
            'task': 'apps.payments.tasks.process_subscription_renewals',
            'group': '📦 Subscription Lifecycle',
            'danger': False,
        },
        {
            'id': 'sync_razorpay_subscriptions',
            'label': 'Sync Razorpay Subscriptions',
            'description': 'Syncs local subscription status with Razorpay API. Runs every 6h.',
            'task': 'apps.payments.tasks.sync_razorpay_subscriptions',
            'group': '📦 Subscription Lifecycle',
            'danger': False,
        },
        {
            'id': 'apply_scheduled_plan_changes',
            'label': 'Apply Scheduled Plan Changes',
            'description': 'Applies pending downgrade/upgrade plan changes when renewal date is reached. Runs hourly.',
            'task': 'apps.payments.tasks.apply_scheduled_plan_changes',
            'group': '📦 Subscription Lifecycle',
            'danger': False,
        },

        # ── Token Management ────────────────────────────────────────────────
        {
            'id': 'reset_daily_token_usage',
            'label': 'Reset Daily Token Usage',
            'description': 'Resets tokens_used_today to 0 for all active/trial subscriptions. Runs at midnight.',
            'task': 'apps.payments.tasks.reset_daily_token_usage',
            'group': '🪙 Token Management',
            'danger': True,  # Dangerous: resets live counters
        },
        {
            'id': 'check_auto_refill_thresholds',
            'label': 'Check Auto-Refill Thresholds',
            'description': 'Finds users below their auto-refill threshold and triggers token purchase. Runs every 15min.',
            'task': 'apps.payments.tasks.check_auto_refill_thresholds',
            'group': '🪙 Token Management',
            'danger': False,
        },
        {
            'id': 'expire_unused_referral_credits',
            'label': 'Expire Unused Referral Credits',
            'description': 'Expires old unprocessed referral credits. Runs Monday 2AM.',
            'task': 'apps.payments.tasks.expire_unused_referral_credits',
            'group': '🪙 Token Management',
            'danger': False,
        },

        # ── Payment Cleanup ─────────────────────────────────────────────────
        {
            'id': 'cleanup_stale_pending_payments',
            'label': 'Cleanup Stale Pending Payments',
            'description': 'Marks pending payments older than 2 hours as expired (abandoned Razorpay checkouts). Runs hourly.',
            'task': 'apps.payments.tasks.cleanup_stale_pending_payments',
            'group': '🧹 Payment Cleanup',
            'danger': False,
        },
        {
            'id': 'generate_monthly_invoices',
            'label': 'Generate Monthly Invoices',
            'description': 'Generates invoice numbers for successful payments that are missing one. Runs daily.',
            'task': 'apps.payments.tasks.generate_monthly_invoices',
            'group': '🧹 Payment Cleanup',
            'danger': False,
        },
        {
            'id': 'cleanup_old_usage_records',
            'label': 'Cleanup Old Usage Records',
            'description': 'Removes very old token usage records to keep the DB lean. Runs weekly Sunday 3:30AM.',
            'task': 'apps.payments.tasks.cleanup_old_usage_records',
            'group': '🧹 Payment Cleanup',
            'danger': False,
        },

        # ── Billing & Analytics ─────────────────────────────────────────────
        {
            'id': 'generate_monthly_billing_report',
            'label': 'Generate Monthly Billing Report',
            'description': 'Emails admin a full billing report: revenue, churn, MRR, token stats. Runs 1st of month.',
            'task': 'apps.payments.tasks.generate_monthly_billing_report',
            'group': '📊 Billing & Analytics',
            'danger': False,
        },
        {
            'id': 'generate_usage_analytics',
            'label': 'Generate Usage Analytics',
            'description': 'Computes and stores usage analytics snapshots. Runs daily 5AM.',
            'task': 'apps.payments.tasks.generate_usage_analytics',
            'group': '📊 Billing & Analytics',
            'danger': False,
        },
        {
            'id': 'calculate_revenue_metrics',
            'label': 'Calculate Revenue Metrics',
            'description': 'Calculates and caches MRR, ARR, ARPU and other revenue KPIs. Runs daily 6AM.',
            'task': 'apps.payments.tasks.calculate_revenue_metrics',
            'group': '📊 Billing & Analytics',
            'danger': False,
        },

        # ── Notifications ───────────────────────────────────────────────────
        {
            'id': 'send_downgrade_warnings',
            'label': 'Send Downgrade Warnings',
            'description': 'Sends in-app notification to users with a scheduled downgrade happening in 3 days. Runs 10AM daily.',
            'task': 'apps.payments.tasks.send_downgrade_warnings',
            'group': '🔔 Notifications',
            'danger': False,
        },

        # ── Security ────────────────────────────────────────────────────────
        {
            'id': 'detect_suspicious_token_activity',
            'label': 'Detect Suspicious Token Activity',
            'description': 'Scans for abnormal token consumption patterns and alerts admin via email. Runs every 4h.',
            'task': 'apps.payments.tasks.detect_suspicious_token_activity',
            'group': '🔒 Security',
            'danger': False,
        },

        # ── Email Tasks ─────────────────────────────────────────────────────
        {
            'id': 'cleanup_old_email_logs',
            'label': 'Cleanup Old Email Logs',
            'description': 'Deletes EmailLog records older than 90 days. Runs daily 3:30AM.',
            'task': 'apps.payments.receipt.email_tasks.cleanup_old_email_logs',
            'group': '📧 Email Tasks',
            'danger': False,
        },
        {
            'id': 'send_email_analytics_report',
            'label': 'Send Email Analytics Report',
            'description': 'Emails admin a weekly report of email send/fail counts by type. Runs Monday 8AM.',
            'task': 'apps.payments.receipt.email_tasks.send_email_analytics_report',
            'group': '📧 Email Tasks',
            'danger': False,
        },
    ]

    # ── Custom URLs ───────────────────────────────────────────────────────────

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'run-task/<str:task_id>/',
                self.admin_site.admin_view(self.run_task_view),
                name='payments_run_celery_task',
            ),
        ]
        return custom_urls + urls

    # ── Task Execution View ───────────────────────────────────────────────────

    def run_task_view(self, request, task_id):
        """
        Called when admin clicks Run Now.
        Finds the task definition, sends it to Celery, shows success/error message.
        """
        task_def = next(
            (t for t in self.PAYMENT_TASKS if t['id'] == task_id),
            None
        )

        if not task_def:
            messages.error(request, f'❌ Unknown task ID: "{task_id}". Has it been added to PAYMENT_TASKS?')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '../'))

        try:
            from celery import current_app
            result = current_app.send_task(task_def['task'])
            messages.success(
                request,
                f'✅ Task "{task_def["label"]}" was queued successfully! '
                f'Celery Task ID: {result.id} — check your worker terminal for output.'
            )
        except Exception as exc:
            messages.error(
                request,
                f'❌ Failed to queue "{task_def["label"]}": {str(exc)}. '
                f'Is Celery worker running? Is Redis up?'
            )

        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '../'))

    # ── Override Changelist to Show Dashboard ────────────────────────────────

    def changelist_view(self, request, extra_context=None):
        """
        Replace the default model list view with our task runner dashboard.
        """
        # Build grouped task dict for the template
        groups = {}
        for task in self.PAYMENT_TASKS:
            g = task['group']
            if g not in groups:
                groups[g] = []
            groups[g].append(task)

        context = {
            **self.admin_site.each_context(request),
            'title': '⚙️ Payment Celery Task Runner',
            'task_groups': groups,
            'opts': self.model._meta,
            'has_permission': True,
        }
        return render(request, 'admin/payments/task_runner.html', context)

    # ── Disable All Standard Admin Operations ────────────────────────────────

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CeleryTaskRunner)
class CeleryTaskRunnerAdmin(PaymentTaskRunnerAdminBase):
    """
    Registered admin for the proxy model.
    This is what actually shows up in /admin/payments/celerytaskrunner/
    """
    pass


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    """Enhanced admin for payment methods with full field visibility"""
    list_display = [
        'user', 'method_type', 'get_method_details', 
        'is_default', 'is_active', 'display_created_at'
    ]
    list_filter = ['method_type', 'is_default', 'is_active', 'card_network', 'created_at']
    search_fields = [
        'user__username', 'user__email', 'razorpay_payment_id', 
        'last4', 'card_network', 'card_issuer', 'upi_vpa', 'bank_name', 'wallet_name'
    ]
    readonly_fields = [
        'razorpay_payment_id', 'method_type', 
        'last4', 'card_network', 'card_issuer', 'card_type',
        'upi_vpa', 'bank_name', 'wallet_name',
        'email', 'contact',
        'created_at', 'updated_at', 'last_used_at'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'email', 'contact')
        }),
        ('Payment Details', {
            'fields': ('razorpay_payment_id', 'method_type')
        }),
        ('Card Information', {
            'fields': ('last4', 'card_network', 'card_issuer', 'card_type'),
            'classes': ('collapse',)
        }),
        ('UPI Information', {
            'fields': ('upi_vpa',),
            'classes': ('collapse',)
        }),
        ('NetBanking Information', {
            'fields': ('bank_name',),
            'classes': ('collapse',)
        }),
        ('Wallet Information', {
            'fields': ('wallet_name',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_default', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_used_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_method_details(self, obj):
        """Display method-specific details"""
        if obj.method_type == 'card':
            return f"{obj.card_network} •••• {obj.last4}"
        elif obj.method_type == 'upi':
            return obj.upi_vpa
        elif obj.method_type == 'netbanking':
            return obj.bank_name
        elif obj.method_type == 'wallet':
            return obj.wallet_name
        return '-'
    get_method_details.short_description = 'Details'
    
    def display_created_at(self, obj):
        """Display created_at in IST"""
        if obj.created_at:
            local_time = localtime(obj.created_at)
            return local_time.strftime('%b %d, %Y, %I:%M %p IST')
        return '-'
    display_created_at.short_description = 'Created At'
    display_created_at.admin_order_field = 'created_at'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('user')


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    """Admin interface for subscription plans"""
    list_display = [
        'display_name', 'name', 'monthly_price', 'annual_price',
        'is_active', 'sort_order',
    ]
    list_filter = ['is_active', 'name']
    search_fields = ['display_name', 'description']
    ordering = ['sort_order', 'monthly_price']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'display_name', 'description', 'is_active', 'sort_order')
        }),
        ('Pricing', {
            'fields': ('monthly_price', 'annual_price')
        }),
        ('Features', {
            'fields': ('features',),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    """
    Admin interface for UserSubscription.
    - Colour-coded status badges in list view
    - IST timestamps throughout
    - Timezone diagnostic panel in detail view
    - Force-expire action for testing
    """

    # ── List view columns ─────────────────────────────────────────────────────
    list_display = [
        'user',
        'plan',
        'coloured_status',       # ← replaces plain 'status'
        'billing_cycle',
        'display_period_end',
        'is_period_expired',     # ← new: shows ✅/❌ expired flag
        'auto_renew',
        'is_trial',
    ]

    list_filter  = ['status', 'billing_cycle', 'plan', 'is_trial', 'auto_renew']
    search_fields = ['user__username', 'user__email', 'razorpay_subscription_id']
    ordering      = ['-created_at']

    readonly_fields = [
        'created_at', 'updated_at',
        'razorpay_subscription_id', 'razorpay_customer_id',
        'timezone_diagnostic',   # ← new: shows UTC vs IST panel
    ]

    date_hierarchy = 'created_at'

    fieldsets = (
        ('⚠️ Timezone Diagnostic', {
            'fields': ('timezone_diagnostic',),
            'description': (
                'This panel shows exactly what time Django thinks it is and what '
                'is stored in the DB — use this to debug expiry issues.'
            ),
        }),
        ('User & Plan', {
            'fields': ('user', 'plan', 'billing_cycle', 'status')
        }),
        ('Billing Dates', {
            'fields': (
                'start_date', 'current_period_start', 'current_period_end',
                'next_billing_date', 'cancelled_at'
            )
        }),
        ('Razorpay Integration', {
            'fields': ('razorpay_subscription_id', 'razorpay_customer_id'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('auto_renew', 'is_trial', 'trial_ends_at')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = [
        'reset_daily_usage',
        'reset_monthly_usage',
        'add_bonus_tokens',
        'force_expire_now',
        'suspend_account',
    ]

    # ── Coloured status badge ─────────────────────────────────────────────────

    STATUS_COLOURS = {
        'active':    ('#16a34a', '#dcfce7'),   # green
        'trial':     ('#0369a1', '#e0f2fe'),   # blue
        'expired':   ('#dc2626', '#fee2e2'),   # red
        'cancelled': ('#d97706', '#fef3c7'),   # amber
        'suspended': ('#7c3aed', '#ede9fe'),   # purple
    }

    def coloured_status(self, obj):
        colour, bg = self.STATUS_COLOURS.get(obj.status, ('#374151', '#f3f4f6'))
        label = obj.get_status_display()
        return format_html(
            '<span style="'
            'display:inline-block;padding:3px 10px;border-radius:12px;'
            'font-size:11px;font-weight:700;letter-spacing:.04em;'
            'color:{};background:{};'
            '">{}</span>',
            colour, bg, label
        )
    coloured_status.short_description = 'Status'
    coloured_status.admin_order_field = 'status'

    # ── Period-end display (IST) ──────────────────────────────────────────────

    def display_period_end(self, obj):
        if not obj.current_period_end:
            return format_html('<span style="color:#9ca3af">—</span>')
        local_time = localtime(obj.current_period_end)
        now        = timezone.now()
        is_past    = obj.current_period_end < now

        colour = '#dc2626' if is_past else '#16a34a'
        icon   = '⚠️ '    if is_past else ''
        return format_html(
            '<span style="color:{};font-weight:{};">{}{}</span>',
            colour,
            '700' if is_past else '400',
            icon,
            local_time.strftime('%d %b %Y, %I:%M %p IST'),
        )
    display_period_end.short_description = 'Period End (IST)'
    display_period_end.admin_order_field = 'current_period_end'

    # ── Is period expired flag ────────────────────────────────────────────────

    def is_period_expired(self, obj):
        if not obj.current_period_end:
            return format_html('<span style="color:#9ca3af">—</span>')
        now     = timezone.now()
        is_past = obj.current_period_end < now
        if is_past:
            return format_html(
                '<span style="color:#dc2626;font-weight:700;" '
                'title="period_end is in the past — task SHOULD expire this">'
                '❌ PAST</span>'
            )
        return format_html(
            '<span style="color:#16a34a;" '
            'title="period_end is still in the future">'
            '✅ Future</span>'
        )
    is_period_expired.short_description = 'Period Expired?'

    # ── Timezone diagnostic panel (shown inside the detail form) ─────────────

    def timezone_diagnostic(self, obj):
        import pytz
        ist         = pytz.timezone('Asia/Kolkata')
        now_utc     = timezone.now()
        now_ist     = now_utc.astimezone(ist)

        period_end_utc = obj.current_period_end
        period_end_ist = period_end_utc.astimezone(ist) if period_end_utc else None
        is_past        = period_end_utc < now_utc if period_end_utc else False
        task_would_run = is_past and obj.status in ('active', 'trial')

        def row(label, value, highlight=False):
            bg = '#fef9c3' if highlight else 'transparent'
            return f'<tr style="background:{bg}"><td style="padding:4px 12px;color:#6b7280;width:220px">{label}</td><td style="padding:4px 12px;font-family:monospace;font-weight:600">{value}</td></tr>'

        rows = [
            row('Django TIME_ZONE (settings.py)', 'Asia/Kolkata (should be this)'),
            row('Now — UTC',   now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')),
            row('Now — IST',   now_ist.strftime('%Y-%m-%d %H:%M:%S IST')),
            row('period_end stored (UTC)',
                period_end_utc.strftime('%Y-%m-%d %H:%M:%S UTC') if period_end_utc else '—'),
            row('period_end display (IST)',
                period_end_ist.strftime('%Y-%m-%d %H:%M:%S IST') if period_end_ist else '—'),
            row('period_end < now?',
                '✅ YES — period has ended' if is_past else '❌ NO — still in future',
                highlight=True),
            row('current status', obj.status),
            row('auto_renew', str(obj.auto_renew)),
            row('Task would expire this subscription?',
                '✅ YES' if task_would_run else '❌ NO — check status or period_end',
                highlight=True),
        ]

        html = (
            '<table style="border-collapse:collapse;font-size:13px;'
            'border:1px solid #e5e7eb;border-radius:6px;overflow:hidden;'
            'background:#f9fafb;width:100%;max-width:700px">'
            + ''.join(rows) +
            '</table>'
            '<p style="font-size:12px;color:#6b7280;margin-top:8px">'
            'When you set <strong>current_period_end</strong> in admin, type the date/time '
            'in <strong>UTC</strong> (subtract 5:30 from your IST time).<br>'
            'Example: if it is 10:00 PM IST now, type <code>2025-02-22 16:30:00</code> to expire immediately.'
            '</p>'
        )
        return mark_safe(html)

    timezone_diagnostic.short_description = 'Timezone Diagnostic'

    # ── Force expire action ───────────────────────────────────────────────────

    def force_expire_now(self, request, queryset):
        count = 0
        for sub in queryset:
            if sub.status in ('active', 'trial'):
                sub.status           = 'expired'
                sub.tokens_remaining = 0
                sub.bonus_tokens     = 0
                sub.save(update_fields=['status', 'tokens_remaining', 'bonus_tokens'])
                count += 1
        self.message_user(
            request,
            f'✅ Force-expired {count} subscription(s). Status = expired, tokens = 0.',
            messages.SUCCESS,
        )
    force_expire_now.short_description = '⛔ Force expire now (bypass task, for testing)'

    # ── Suspend account action ────────────────────────────────────────────────

    def suspend_account(self, request, queryset):
        from payments.tasks import _send_task_notification

        count = 0
        for sub in queryset:
            if sub.status in ('active', 'trial'):
                sub.status = 'suspended'
                sub.tokens_remaining = 0
                sub.bonus_tokens = 0
                sub.save(update_fields=['status', 'tokens_remaining', 'bonus_tokens'])
                count += 1

                # Send account suspended email to the user
                try:
                    from django.conf import settings as django_settings
                    _send_task_notification(
                        user=sub.user,
                        email_type='subscription_suspended',
                        subject='Your dm-me account has been suspended',
                        context={
                            'plan_name': sub.plan.display_name,
                            'failed_count': sub.failed_payment_count or 0,
                            'reactivate_url': f"{django_settings.FRONTEND_URL}/pricing",
                            'plain_message': (
                                f"Hi {sub.user.first_name or sub.user.username},\n\n"
                                f"Your {sub.plan.display_name} subscription has been suspended "
                                f"by the admin. You can no longer create or edit projects.\n\n"
                                f"Update your payment method to reactivate: "
                                f"{django_settings.FRONTEND_URL}/pricing"
                            ),
                            'log_metadata': {
                                'subscription_id': str(sub.id),
                                'suspended_by': 'admin',
                            },
                        },
                        template_name='emails/account_suspended.html',
                    )
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"Failed to send suspension email for {sub.id}: {e}")

        self.message_user(
            request,
            f'🚫 Suspended {count} account(s). Users have been notified via email.',
            messages.SUCCESS if count else messages.WARNING,
        )
    suspend_account.short_description = '🚫 Suspend account (sends email notification)'

    # ── Existing actions (keep these) ─────────────────────────────────────────

    def reset_daily_usage(self, request, queryset):
        count = 0
        for subscription in queryset:
            subscription.reset_daily_usage()
            count += 1
        self.message_user(request, f'Reset daily usage for {count} subscriptions')
    reset_daily_usage.short_description = 'Reset daily token usage'

    def reset_monthly_usage(self, request, queryset):
        count = 0
        for subscription in queryset:
            subscription.reset_monthly_usage()
            count += 1
        self.message_user(request, f'Reset monthly usage for {count} subscriptions')
    reset_monthly_usage.short_description = 'Reset monthly token usage'

    def add_bonus_tokens(self, request, queryset):
        bonus_amount = 100
        count = 0
        for subscription in queryset:
            subscription.add_bonus_tokens(bonus_amount)
            count += 1
        self.message_user(request, f'Added {bonus_amount} bonus tokens to {count} subscriptions')
    add_bonus_tokens.short_description = 'Add 100 bonus tokens'



@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for payments - WITH TIMEZONE FIX"""
    list_display = [
        'invoice_number', 'user', 'payment_type', 'amount', 'currency',
        'status', 'tokens_purchased', 'display_created_at', 'display_completed_at'
    ]
    list_filter = ['status', 'payment_type', 'currency', 'created_at']
    search_fields = [
        'user__username', 'user__email', 'invoice_number',
        'razorpay_order_id', 'razorpay_payment_id'
    ]
    
    readonly_fields = [
        'invoice_number', 'tokens_purchased', 'billing_address', 'metadata',
        'subscription',
        'created_at', 'updated_at', 'completed_at',
        'razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature'
    ]
    
    exclude = ['subscription']
    date_hierarchy = 'created_at'
    
    actions = ['trigger_receipt_email']
    
    fieldsets = (
        ('Payment Details', {
            'fields': (
                'user', 'payment_type',
                'amount', 'currency', 'status'
            )
        }),
        ('Razorpay Details', {
            'fields': (
                'razorpay_order_id', 'razorpay_payment_id',
                'razorpay_signature'
            ),
            'classes': ('collapse',)
        }),
        ('Token Purchase', {
            'fields': ('tokens_purchased',)
        }),
        ('Invoice', {
            'fields': ('invoice_number', 'billing_address')
        }),
        ('Status & Metadata', {
            'fields': ('failure_reason', 'metadata')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def display_created_at(self, obj):
        """Display created_at in IST"""
        if obj.created_at:
            local_time = localtime(obj.created_at)
            return local_time.strftime('%b %d, %Y, %I:%M %p IST')
        return '-'
    display_created_at.short_description = 'Created At'
    display_created_at.admin_order_field = 'created_at'
    
    def display_completed_at(self, obj):
        """Display completed_at in IST"""
        if obj.completed_at:
            local_time = localtime(obj.completed_at)
            return local_time.strftime('%b %d, %Y, %I:%M %p IST')
        return '-'
    display_completed_at.short_description = 'Completed At'
    display_completed_at.admin_order_field = 'completed_at'

    def trigger_receipt_email(self, request, queryset):
        """
        Admin action: select one or more payments from the list,
        then choose this action to queue a receipt email for each.
        """
        from payments.receipt.email_tasks import send_payment_receipt_email
        
        queued = 0
        skipped = 0
        
        for payment in queryset:
            if payment.status == 'success':
                send_payment_receipt_email.delay(str(payment.id))
                queued += 1
            else:
                skipped += 1
        
        if queued:
            self.message_user(
                request,
                f'✅ Queued receipt email for {queued} payment(s). Check worker terminal.',
                messages.SUCCESS
            )
        if skipped:
            self.message_user(
                request,
                f'⚠️ Skipped {skipped} payment(s) — only status=success payments get receipts.',
                messages.WARNING
            )
    trigger_receipt_email.short_description = '📧 Send payment receipt email (via Celery)'
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of payment records / for security return false"""
        return request.user.is_superuser


# @admin.register(TokenPackage)
# class TokenPackageAdmin(admin.ModelAdmin):
#     """Admin interface for token packages"""
#     list_display = [
#         'name', 'token_count', 'price_inr', 'price_usd',
#         'bonus_percentage', 'is_active', 'is_featured', 'sort_order'
#     ]
#     list_filter = ['is_active', 'is_featured']
#     search_fields = ['name', 'description']
#     ordering = ['sort_order', 'token_count']
    
#     fieldsets = (
#         ('Package Information', {
#             'fields': ('name', 'description', 'token_count')
#         }),
#         ('Pricing', {
#             'fields': ('price_inr', 'price_usd', 'bonus_percentage')
#         }),
#         ('Display Settings', {
#             'fields': ('is_active', 'is_featured', 'sort_order')
#         }),
#     )


# @admin.register(TokenUsage)
# class TokenUsageAdmin(admin.ModelAdmin):
#     """Admin interface for token usage"""
#     list_display = [
#         'user', 'tokens_used', 'tokens_requested', 'description',
#         'feature', 'ai_model_used', 'status', 'display_created_at'
#     ]
#     list_filter = ['status', 'feature', 'ai_model_used', 'created_at']
#     search_fields = ['user__username', 'description', 'project_id']
#     readonly_fields = ['created_at']
#     date_hierarchy = 'created_at'
    
#     fieldsets = (
#         ('Usage Details', {
#             'fields': (
#                 'user', 'subscription', 'tokens_used', 'tokens_requested',
#                 'description', 'status'
#             )
#         }),
#         ('Context', {
#             'fields': ('project_id', 'feature', 'failure_reason')
#         }),
#         ('AI Model Details', {
#             'fields': ('ai_model_used', 'prompt_tokens', 'completion_tokens'),
#             'classes': ('collapse',)
#         }),
#         ('Metadata', {
#             'fields': ('metadata', 'created_at'),
#             'classes': ('collapse',)
#         }),
#     )
    
#     def display_created_at(self, obj):
#         """Display created_at in IST"""
#         if obj.created_at:
#             local_time = localtime(obj.created_at)
#             return local_time.strftime('%b %d, %Y, %I:%M %p IST')
#         return '-'
#     display_created_at.short_description = 'Created At'
#     display_created_at.admin_order_field = 'created_at'
    
#     def has_add_permission(self, request):
#         """Prevent manual creation of usage records"""
#         return False
    
#     def has_delete_permission(self, request, obj=None):
#         """Prevent deletion of usage records"""
#         return False


# WebhookLog admin is already registered in analytics/admin.py
# @admin.register(WebhookLog)
# class WebhookLogAdmin(admin.ModelAdmin):
#     """Admin interface for webhook logs"""
#     list_display = [
#         'event_type', 'event_id', 'processed',
#         'user', 'display_created_at', 'display_processed_at'
#     ]
#     list_filter = ['event_type', 'processed', 'created_at']
#     search_fields = ['event_id', 'event_type']
#     readonly_fields = ['created_at', 'processed_at']
#     date_hierarchy = 'created_at'
#     fieldsets = (
#         ('Event Details', {
#             'fields': ('event_type', 'event_id', 'payload')
#         }),
#         ('Processing', {
#             'fields': ('processed', 'processed_at', 'processing_error')
#         }),
#         ('Related Objects', {
#             'fields': ('payment', 'user'),
#             'classes': ('collapse',)
#         }),
#         ('Metadata', {
#             'fields': ('created_at',),
#             'classes': ('collapse',)
#         }),
#     )
#     def display_created_at(self, obj):
#         if obj.created_at:
#             local_time = localtime(obj.created_at)
#             return local_time.strftime('%b %d, %Y, %I:%M %p IST')
#         return '-'
#     display_created_at.short_description = 'Created At'
#     display_created_at.admin_order_field = 'created_at'
#     def display_processed_at(self, obj):
#         if obj.processed_at:
#             local_time = localtime(obj.processed_at)
#             return local_time.strftime('%b %d, %Y, %I:%M %p IST')
#         return '-'
#     display_processed_at.short_description = 'Processed At'
#     display_processed_at.admin_order_field = 'processed_at'
#     def has_add_permission(self, request):
#         return False



@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    """Admin interface for managing tax rates by country."""
    list_display = ['country_code', 'tax_name', 'rate', 'is_active', 'updated_at']
    list_filter = ['is_active']
    search_fields = ['country_code', 'tax_name']
    list_editable = ['tax_name', 'rate', 'is_active']
    ordering = ['country_code']