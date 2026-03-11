"""
Serializers for Payment Models
"""
from rest_framework import serializers
from .models import (
    SubscriptionPlan, UserSubscription, Payment,
    PaymentMethod
)



class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Serializer for subscription plans"""
    annual_discount = serializers.SerializerMethodField()
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'display_name', 'description',
            'monthly_price', 'annual_price', 'annual_discount',
            'features', 'is_active', 'sort_order',
            'allow_self_service_changes'
        ]

    
    def get_annual_discount(self, obj):
        """Get annual discount percentage"""
        return obj.get_annual_discount_percentage()


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for user subscriptions"""
    plan = SubscriptionPlanSerializer(read_only=True)
    plan_name = serializers.CharField(source='plan.display_name', read_only=True)
    days_until_renewal = serializers.SerializerMethodField()
    latest_payment_id = serializers.SerializerMethodField()

    
    class Meta:
        model = UserSubscription
        fields = [
            'id', 'plan', 'plan_name', 'billing_cycle', 'status',
            'start_date', 'current_period_start', 'current_period_end',
            'next_billing_date', 'auto_renew', 'is_trial', 'trial_ends_at',
            'days_until_renewal', 'created_at', 'latest_payment_id'
        ]

    
    def get_days_until_renewal(self, obj):
        """Calculate days until next billing"""
        if obj.next_billing_date:
            from django.utils import timezone
            delta = obj.next_billing_date - timezone.now()
            return max(0, delta.days)
        return None
    
    def get_usage_percentage(self, obj):
        """Calculate percentage of tokens used this month (placeholder until token fields are re-added)"""
        return 0

        
    def get_latest_payment_id(self, obj):
        """Get the ID of the most recent successful payment for invoicing"""
        # First try payments directly linked to this subscription
        latest_payment = obj.payment_set.filter(status='success').order_by('-completed_at').first()
        
        # Fallback to user's general payments (e.g. if the explicit link is missing)
        if not latest_payment:
            from payments.models import Payment
            latest_payment = Payment.objects.filter(
                user=obj.user,
                status='success'
            ).order_by('-completed_at').first()
            
        return str(latest_payment.id) if latest_payment else None



class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for payments"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    subscription_plan = serializers.CharField(
        source='subscription.plan.display_name',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = Payment
        fields = [
            'id', 'user_name', 'payment_type', 'amount', 'currency',
            'razorpay_order_id', 'razorpay_payment_id', 'status',
            'tokens_purchased', 'subscription_plan', 'invoice_number',
            'created_at', 'completed_at'
        ]


# class TokenPackageSerializer(serializers.ModelSerializer):
#     """Serializer for token packages"""
#     total_tokens = serializers.SerializerMethodField()
    
#     class Meta:
#         model = TokenPackage
#         fields = [
#             'id', 'name', 'description', 'token_count',
#             'price_inr', 'price_usd', 'bonus_percentage',
#             'total_tokens', 'is_featured'
#         ]
    
#     def get_total_tokens(self, obj):
#         """Get total tokens including bonus"""
#         return obj.get_total_tokens()


# class TokenUsageSerializer(serializers.ModelSerializer):
#     """Serializer for token usage records"""
    
#     class Meta:
#         model = TokenUsage
#         fields = [
#             'id', 'tokens_used', 'tokens_requested', 'description',
#             'project_id', 'feature', 'ai_model_used',
#             'prompt_tokens', 'completion_tokens', 'status',
#             'failure_reason', 'created_at'
#         ]


# class WebhookLogSerializer(serializers.ModelSerializer):
#     """Serializer for webhook logs"""
    
#     class Meta:
#         model = WebhookLog
#         fields = [
#             'id', 'event_type', 'event_id', 'payload',
#             'processed', 'processed_at', 'processing_error',
#             'created_at'
#         ]

class PaymentMethodSerializer(serializers.ModelSerializer):
    """Serializer for payment methods"""
    display_name = serializers.CharField(source='get_display_name', read_only=True)
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'method_type', 'display_name',
            # Card fields
            'last4', 'card_network', 'card_issuer', 'card_type',
            # UPI fields
            'upi_vpa',
            # NetBanking fields
            'bank_name',
            # Wallet fields
            'wallet_name',
            # Common fields
            'email', 'contact',
            'is_default', 'is_active',
            'created_at', 'last_used_at'
        ]
        read_only_fields = ['id', 'created_at', 'last_used_at', 'display_name']