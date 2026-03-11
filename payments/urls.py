from django.urls import path
from django.conf import settings
from .views import (
    ApplyReferralCodeView, CancelScheduledChangeView,
    GetCurrencyConversionView, GetPlanChangePreviewView, PaymentAnalyticsView,
    PaymentMethodsView, RecordPaymentFailureView, ReferralCodeView, ReferralStatsView,
    SubscriptionPlansView, UpgradePlanView, UserSubscriptionView, CreateSubscriptionView,
   
    VerifyPaymentView,  CancelSubscriptionView,
    RazorpayWebhookView, PaymentHistoryView, DownloadInvoiceView
)

app_name = 'payments'

urlpatterns = [
    # Subscription Plans
    path('plans/', SubscriptionPlansView.as_view(), name='subscription_plans'),
    
    # User Subscription Management
    path('subscription/', UserSubscriptionView.as_view(), name='user_subscription'),
    path('subscription/create/', CreateSubscriptionView.as_view(), name='create_subscription'),
    path('subscription/cancel/', CancelSubscriptionView.as_view(), name='cancel_subscription'),
    # path('auto-refill/', AutoRefillSettingsView.as_view(), name='auto_refill'),

    # Payment Verification
    path('verify/', VerifyPaymentView.as_view(), name='verify-payment'),
    path('payment-methods/', PaymentMethodsView.as_view(), name='payment_methods'),
    path('payment-methods/<uuid:method_id>/', PaymentMethodsView.as_view(), name='delete_payment_method'),

    # Subscription Plan Changes
    path('subscription/upgrade/', UpgradePlanView.as_view(), name='upgrade_plan'),
    path('subscription/change-preview/', GetPlanChangePreviewView.as_view(), name='plan_change_preview'),
    path('subscription/cancel-scheduled-change/', CancelScheduledChangeView.as_view(), name='cancel_scheduled_change'),

    # Referral System
    path('referral/code/', ReferralCodeView.as_view(), name='referral_code'),
    path('referral/apply/', ApplyReferralCodeView.as_view(), name='apply_referral'),
    path('referral/stats/', ReferralStatsView.as_view(), name='referral_stats'),

    # Analytics
    path('analytics/', PaymentAnalyticsView.as_view(), name='analytics'),

    
    # path('test/webhook-signature/', GenerateWebhookSignatureView.as_view()),

    # Token Balance
    # path('token-balance/', UserTokenBalanceView.as_view(), name='token-balance'),
    # path('token-balance/realtime/', UserTokenBalanceRealtimeView.as_view(), name='token_balance_realtime'),

    # Payment Failure Recording
    path('verify/failure/', RecordPaymentFailureView.as_view(), name='record_payment_failure'),

    # # Token Packages
    # path('tokens/packages/', TokenPackagesView.as_view(), name='token_packages'),
    # path('tokens/purchase/', PurchaseTokensView.as_view(), name='purchase_tokens'),
    # path('tokens/verify/', VerifyTokenPurchaseView.as_view(), name='verify_token_purchase'),
    # path('tokens/usage/', TokenUsageHistoryView.as_view(), name='token_usage'),

    # Payment History
    path('history/', PaymentHistoryView.as_view(), name='payment_history'),
    path('invoice/<uuid:payment_id>/download/', DownloadInvoiceView.as_view(), name='download_invoice'),
    
    # Razorpay Webhook
    path('webhook/razorpay/', RazorpayWebhookView.as_view(), name='razorpay_webhook'),

    
    # Currency
    path('currency/convert/', GetCurrencyConversionView.as_view(), name='currency_convert'),

]

if settings.DEBUG:
    from .views import GenerateTestSignatureView, GenerateWebhookSignatureView

    urlpatterns += [
        path('test/generate-signature/', GenerateTestSignatureView.as_view(), name='test_signature'),
        path('test/webhook-signature/', GenerateWebhookSignatureView.as_view(), name='test_webhook_signature'),
    ]