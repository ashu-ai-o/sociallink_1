"""
Payment Views and API Endpoints
"""
# from django.db import connection
from datetime import datetime, timedelta
import json
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .receipt.email_tasks import send_payment_receipt_email, send_payment_failure_email
import logging
from django.http import HttpResponse

from payments.currency_service import CurrencyService
from .razorpay_service import RazorpayService
from payments.utils import calculate_proration
import hmac
import hashlib
from django.conf import settings
from .models import (
    PaymentMethod, Referral, ReferralCode, SubscriptionPlan, UserSubscription, Payment
)
from analytics.models import WebhookLog
from .razorpay_service import RazorpayService
from .serializers import (
    PaymentMethodSerializer, SubscriptionPlanSerializer, UserSubscriptionSerializer,
    PaymentSerializer
)
from .audit import log_payment_event, get_client_ip
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
logger = logging.getLogger(__name__)

class PaymentBurstThrottle(UserRateThrottle):
    """Tight limit for payment-critical endpoints (signature verification, purchases)"""
    rate = '100/minute'

class PaymentSustainedThrottle(UserRateThrottle):
    """Sustained limit to prevent order spamming over longer windows"""
    rate = '100/hour'

class WebhookThrottle(AnonRateThrottle):
    """Rate limit for webhook endpoint (unauthenticated, from Razorpay servers)"""
    rate = '100/minute'

class SubscriptionPlansView(APIView):
    """
    Get all available subscription plans
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """List all active subscription plans"""
        plans = SubscriptionPlan.objects.filter(is_active=True)
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response({
            'success': True,
            'plans': serializer.data
        })


class UserSubscriptionView(APIView):
    """
    Get current user's subscription details
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user's current subscription"""
        try:
            subscription = UserSubscription.objects.select_related('plan').get(
                user=request.user
            )
            serializer = UserSubscriptionSerializer(subscription)
            return Response({
                'success': True,
                'subscription': serializer.data
            })
        except UserSubscription.DoesNotExist:
            return Response({
                'success': True,
                'subscription': None,
                'message': 'No active subscription'
            })


class CreateSubscriptionView(APIView):
    """Create new subscription or upgrade existing one"""
    permission_classes = [IsAuthenticated]
    throttle_classes = [PaymentBurstThrottle, PaymentSustainedThrottle]

    @transaction.atomic
    def post(self, request):
        """Create subscription with dynamic currency conversion"""
        plan_id = request.data.get('plan_id')
        billing_cycle = request.data.get('billing_cycle', 'monthly')

        if not plan_id:
            return Response({
                'success': False,
                'error': 'plan_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Invalid plan'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get base USD amount
        if billing_cycle == 'annual':
            usd_amount = Decimal(str(plan.annual_price))
        else:
            usd_amount = Decimal(str(plan.monthly_price))

        proration_credit_usd = Decimal('0')
        is_upgrade = False
        
        # Apply Proration if upgrading
        try:
            current_sub = UserSubscription.objects.select_related('plan').get(user=request.user)
            from .services import SubscriptionService
            can_change, reason, is_upgrade = SubscriptionService.validate_plan_change(current_sub, plan, billing_cycle)
            
            if not can_change:
                return Response({
                    'success': False,
                    'error': reason or 'Cannot change to this plan'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            if is_upgrade:
                from .utils import calculate_proration
                proration = calculate_proration(current_sub, plan, billing_cycle)
                usd_amount = proration['prorated_amount_usd']
                proration_credit_usd = proration['credit_amount_usd']
                
        except UserSubscription.DoesNotExist:
            pass


        # ========================================
        # CURRENCY CONVERSION BASED ON USER LOCATION
        # ========================================
        from accounts.session_tracker import SessionTracker
        
        # Get user's IP and country
        ip_address, _ = SessionTracker.get_client_ip(request)
        geo_data = SessionTracker.get_geolocation(ip_address)
        country_code = geo_data.get('country_code', 'US')
        if country_code == 'LOCAL':
            country_code = 'IN'
            
        logger.info(f"User location: {country_code} (IP: {ip_address})")
        
        # Get currency conversion
        currency_service = CurrencyService()
        payment_details = currency_service.get_payment_details(
            usd_amount,
            country_code
        )
        
        local_currency = payment_details['local_currency']
        local_amount = Decimal(str(payment_details['local_amount']))
        exchange_rate = payment_details['exchange_rate']

        # ========================================
        # AUTOMATED TAX CALCULATION
        # ========================================
        from .utils import calculate_tax
        tax_details = calculate_tax(local_amount, country_code)
        
        final_local_amount = tax_details['total_amount']
        tax_name = tax_details['tax_name']
        tax_amount = tax_details['tax_amount']
        tax_rate = tax_details['tax_rate']
        
        logger.info(
            f"Converting ${usd_amount} USD to {local_amount} {local_currency} "
            f"(rate: {exchange_rate}). Tax applied: {tax_amount} ({tax_name}). Final Due: {final_local_amount}"
        )

        # Validate minimum amount
        if final_local_amount < Decimal('1.00'):
            return Response({
                'success': False,
                'error': f'Amount ({final_local_amount} {local_currency}) is less than minimum allowed'
            }, status=status.HTTP_400_BAD_REQUEST)

        razorpay_service = RazorpayService()

        # Get or create customer
        customer_id = None
        try:
            existing_subscription = UserSubscription.objects.get(user=request.user)
            if existing_subscription.razorpay_customer_id:
                customer_id = existing_subscription.razorpay_customer_id
        except UserSubscription.DoesNotExist:
            pass

        if not customer_id:
            customer_result = razorpay_service.create_customer(
                name=request.user.get_full_name() or request.user.username,
                email=request.user.email
            )
            
            if not customer_result['success']:
                error_msg = customer_result.get('error', '')
                if 'already exists' in error_msg.lower():
                    fetch_result = razorpay_service.fetch_customer_by_email(request.user.email)
                    if fetch_result['success'] and fetch_result.get('customers'):
                        customer_id = fetch_result['customers'][0]['id']
                    else:
                        return Response({
                            'success': False,
                            'error': 'Failed to fetch existing customer'
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                else:
                    return Response({
                        'success': False,
                        'error': f'Customer creation failed: {error_msg}'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                customer_id = customer_result['customer']['id']

        # Create Razorpay order with converted currency + tax!
        short_receipt = f'sub{int(timezone.now().timestamp())}'
        order_result = razorpay_service.create_order(
            amount=final_local_amount,
            currency=local_currency,
            receipt=short_receipt,
            notes={
                'user_id': str(request.user.id),
                'plan_id': str(plan.id),
                'billing_cycle': billing_cycle,
                'base_amount_usd': str(usd_amount),
                'exchange_rate': str(exchange_rate),
                'country_code': country_code,
                'proration_credit_usd': str(proration_credit_usd),
                'tax_name': tax_name,
                'tax_amount': str(tax_amount)
            }
        )

        if not order_result['success']:
            return Response({
                'success': False,
                'error': 'Razorpay order creation failed: ' + order_result.get('error', 'Unknown error')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        order = order_result['order']


        Payment.objects.create(
            user=request.user,
            payment_type='subscription',
            amount=usd_amount, # Base USD amount for records
            currency='USD',
            razorpay_order_id=order['id'],
            status='pending',
            metadata={
                'plan_id': str(plan.id),
                'billing_cycle': billing_cycle,
                'local_amount': str(final_local_amount),
                'local_currency': local_currency,
                'exchange_rate': str(exchange_rate),
                'proration_credit_usd': str(proration_credit_usd),
                'tax_rate': str(tax_rate),
                'tax_name': tax_name,
                'tax_amount_local': str(tax_amount),
                'base_local_amount': str(local_amount)
            }
        )

        return Response({
            'success': True,
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'order_id': order['id'],
            'amount': int(final_local_amount * 100),  # In smallest currency unit
            'currency': local_currency,
            'customer_id': customer_id,
            'plan_details': {
                'id': str(plan.id),
                'name': plan.display_name,
                'billing_cycle': billing_cycle
            },
            'conversion_details': payment_details,
            'tax_details': {
                'tax_name': tax_name,
                'tax_rate': float(tax_rate),
                'tax_amount': float(tax_amount),
                'subtotal': float(local_amount),
                'total': float(final_local_amount)
            }
        })
    
# class UserTokenBalanceView(APIView):
#     """
#     Get user's token balance and usage statistics
#     """
#     permission_classes = [IsAuthenticated]
    
#     def get(self, request):
#         """Get current token balance"""
#         try:
#             subscription = UserSubscription.objects.select_related('plan').get(user=request.user)
            
#             # Calculate total available tokens
#             total_available = subscription.tokens_remaining + subscription.bonus_tokens
            
#             # Calculate percentage remaining
#             total_allocation = subscription.plan.monthly_token_credits
#             if total_allocation > 0:
#                 percentage_remaining = (subscription.tokens_remaining / total_allocation) * 100
#             else:
#                 percentage_remaining = 0
            
#             # Calculate total cost from payments
#             from django.db.models import Sum
#             total_cost = Payment.objects.filter(
#                 user=request.user,
#                 status='success'
#             ).aggregate(total=Sum('amount'))['total'] or 0

#             data = {
#                 'success': True,
#                 'tokens': {
#                     'total_available': total_available,
#                     'base_remaining': subscription.tokens_remaining,
#                     'bonus_tokens': subscription.bonus_tokens,
#                     'rollover_tokens': subscription.rollover_tokens,
#                     'used_today': subscription.tokens_used_today,
#                     'used_this_month': subscription.tokens_used_this_month,
#                     'total_used': subscription.total_tokens_used,
#                     'daily_limit': subscription.plan.daily_token_limit,
#                     'monthly_allocation': subscription.plan.monthly_token_credits,
#                     'percentage_remaining': round(percentage_remaining, 2)
#                 },
#                 'plan': {
#                     'name': subscription.plan.display_name,
#                     'billing_cycle': subscription.billing_cycle,
#                     'status': subscription.status
#                 },
#                 'usage': {
#                     'today': subscription.tokens_used_today,
#                     'this_month': subscription.tokens_used_this_month,
#                     'daily_limit': subscription.plan.daily_token_limit,
#                     'daily_remaining': max(0, subscription.plan.daily_token_limit - subscription.tokens_used_today)
#                 },
#                 'total_cost_usd': float(total_cost)
#             }
            
#             return Response(data)
            
#         except UserSubscription.DoesNotExist:
#             # Return default values for users without subscriptions (e.g., new Google OAuth users)
#             return Response({
#                 'success': True,
#                 'tokens': {
#                     'total_available': 0,
#                     'base_remaining': 0,
#                     'bonus_tokens': 0,
#                     'rollover_tokens': 0,
#                     'used_today': 0,
#                     'used_this_month': 0,
#                     'total_used': 0,
#                     'daily_limit': 0,
#                     'monthly_allocation': 0,
#                     'percentage_remaining': 0
#                 },
#                 'plan': {
#                     'name': 'No Active Plan',
#                     'billing_cycle': None,
#                     'status': 'inactive'
#                 },
#                 'usage': {
#                     'today': 0,
#                     'this_month': 0,
#                     'daily_limit': 0,
#                     'daily_remaining': 0
#                 },
#                 'message': 'No active subscription. Please subscribe to a plan.'
#             })

class VerifyPaymentView(APIView):
    """
    Verify and process payment after Razorpay checkout
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [PaymentBurstThrottle, PaymentSustainedThrottle]

    @staticmethod
    def process_successful_payment(payment, razorpay_payment_id, razorpay_signature=None, ip_address=None):
        """
        Delegates to SubscriptionService for activation.
        """
        from .services import SubscriptionService
        return SubscriptionService.activate_subscription(
            payment, razorpay_payment_id, razorpay_signature, ip_address
        )


    def post(self, request):
        """Verify payment signature and activate subscription"""
        try:
            razorpay_order_id = request.data.get('razorpay_order_id')
            razorpay_payment_id = request.data.get('razorpay_payment_id')
            razorpay_signature = request.data.get('razorpay_signature')

            if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
                return Response({
                    'success': False,
                    'error': 'Missing payment details'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Verify signature
            razorpay_service = RazorpayService()
            is_valid = razorpay_service.verify_payment_signature(
                razorpay_order_id,
                razorpay_payment_id,
                razorpay_signature
            )

            if not is_valid:
                return Response({
                    'success': False,
                    'error': 'Invalid payment signature'
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                payment = Payment.objects.get(
                    razorpay_order_id=razorpay_order_id,
                    user=request.user
                )
            except Payment.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Payment record not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if already processed by webhook
            if payment.status == 'success' and payment.subscription:
                return Response({
                    'success': True,
                    'message': 'Payment was already processed successfully',
                    'subscription': {
                        'id': str(payment.subscription.id),
                        'plan': payment.subscription.plan.display_name,
                        'status': payment.subscription.status,
                        'billing_cycle': payment.subscription.billing_cycle,
                        'period_end': payment.subscription.current_period_end.isoformat()
                    },
                    'payment': {
                        'id': str(payment.id),
                        'status': payment.status,
                        'amount': str(payment.amount)
                    }
                })

            success, result, updated_payment = VerifyPaymentView.process_successful_payment(
                payment, razorpay_payment_id, razorpay_signature, get_client_ip(request)
            )

            if not success:
                return Response({
                    'success': False,
                    'error': f'Failed to activate subscription: {result}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({
                'success': True,
                'message': 'Payment verified and subscription activated',
                'subscription': result,
                'payment': {
                    'id': str(updated_payment.id),
                    'status': updated_payment.status,
                    'amount': str(updated_payment.amount)
                }
            })

        except Exception as e:
            logger.error(f"VerifyPaymentView failed: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'Payment verification failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RecordPaymentFailureView(APIView):
    """
    Record payment failure from frontend
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        """Record failed payment attempt"""
        razorpay_order_id = request.data.get('razorpay_order_id')
        error_code = request.data.get('error_code')
        error_description = request.data.get('error_description')
        razorpay_payment_id = request.data.get('razorpay_payment_id') # Optional
        
        if not razorpay_order_id:
             return Response({
                'success': False,
                'error': 'razorpay_order_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Find the payment record
            payment = Payment.objects.get(
                razorpay_order_id=razorpay_order_id,
                user=request.user
            )
            
            # Update payment status
            payment.status = 'failed'
            if razorpay_payment_id:
                payment.razorpay_payment_id = razorpay_payment_id
            
            # Construct meaningful failure reason
            failure_reason = ""
            if error_code:
                failure_reason += f"Code: {error_code} "
            if error_description:
                failure_reason += f"Desc: {error_description}"
            
            payment.failure_reason = failure_reason.strip()
            payment.save()
            
            # Update subscription failure count if it's a subscription payment
            if payment.payment_type == 'subscription' and payment.subscription:
                subscription = payment.subscription
                subscription.last_payment_status = 'failed'
                subscription.failed_payment_count += 1
                subscription.save(update_fields=['last_payment_status', 'failed_payment_count'])
            
            # Send failure email
            try:
                from .receipt.email_tasks import send_payment_failure_email
                logger.info(f"Queuing payment failure email for payment {payment.id}")
                send_payment_failure_email.delay(str(payment.id))
            except Exception as e:
                logger.error(f"Failed to queue failure email: {str(e)}")

            return Response({
                'success': True,
                'message': 'Payment failure recorded'
            })

        except Payment.DoesNotExist:
             return Response({
                'success': False,
                'error': 'Payment order not found'
            }, status=status.HTTP_404_NOT_FOUND)
        

# class TokenPackagesView(APIView):
#     """
#     Get available token packages for one-time purchase
#     """
#     permission_classes = [IsAuthenticated]
    
#     def get(self, request):
#         """List all active token packages"""
#         packages = TokenPackage.objects.filter(is_active=True)
#         serializer = TokenPackageSerializer(packages, many=True)
#         return Response({
#             'success': True,
#             'packages': serializer.data
#         })


# class PurchaseTokensView(APIView):
#     """
#     Purchase additional tokens
#     """
#     permission_classes = [IsAuthenticated]
#     throttle_classes = [PaymentBurstThrottle, PaymentSustainedThrottle]
    
#     @transaction.atomic
#     def post(self, request):
#         """Create order for token purchase"""
#         package_id = request.data.get('package_id')
        
#         if not package_id:
#             return Response({
#                 'success': False,
#                 'error': 'package_id is required'
#             }, status=status.HTTP_400_BAD_REQUEST)
        
#         try:
#             package = TokenPackage.objects.get(id=package_id, is_active=True)
#         except TokenPackage.DoesNotExist:
#             return Response({
#                 'success': False,
#                 'error': 'Invalid package'
#             }, status=status.HTTP_404_NOT_FOUND)
        
#         # Determine currency and price
#         currency = 'USD'  # Can be enhanced based on user location
#         amount = package.get_price_for_currency(currency)
        
#         # Create Razorpay order
#         razorpay_service = RazorpayService()
#         order_result = razorpay_service.create_order(
#             amount=amount,
#             currency=currency,
#             receipt=f'tokens_{request.user.id}_{timezone.now().timestamp()}',
#             notes={
#                 'user_id': str(request.user.id),
#                 'package_id': str(package.id),
#                 'token_count': package.get_total_tokens()
#             }
#         )
        
#         if not order_result['success']:
#             return Response({
#                 'success': False,
#                 'error': f'Failed to create order'
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#         order = order_result['order']
        
#         # Create payment record
#         payment = Payment.objects.create(
#             user=request.user,
#             payment_type='token_purchase',
#             amount=amount,
#             currency=currency,
#             razorpay_order_id=order['id'],
#             tokens_purchased=package.get_total_tokens(),
#             status='pending',
#             metadata={
#                 'package_id': str(package.id),
#                 'package_name': package.name
#             }
#         )
        
#         return Response({
#             'success': True,
#             'order_id': order['id'],
#             'amount': amount,
#             'currency': currency,
#             'payment_id': str(payment.id),
#             'package_name': package.name,
#             'tokens': package.get_total_tokens()
#         })


# class VerifyTokenPurchaseView(APIView):
#     """
#     Verify token purchase payment
#     """
#     permission_classes = [IsAuthenticated]
#     throttle_classes = [PaymentBurstThrottle, PaymentSustainedThrottle]
    
#     @transaction.atomic
#     def post(self, request):
#         """Verify payment and add tokens"""
#         razorpay_order_id = request.data.get('razorpay_order_id')
#         razorpay_payment_id = request.data.get('razorpay_payment_id')
#         razorpay_signature = request.data.get('razorpay_signature')
        
#         if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
#             return Response({
#                 'success': False,
#                 'error': 'Missing payment details'
#             }, status=status.HTTP_400_BAD_REQUEST)
        
#         # Verify signature
#         razorpay_service = RazorpayService()
#         is_valid = razorpay_service.verify_payment_signature(
#             razorpay_order_id,
#             razorpay_payment_id,
#             razorpay_signature
#         )
        
#         if not is_valid:
#             return Response({
#                 'success': False,
#                 'error': 'Invalid payment signature'
#             }, status=status.HTTP_400_BAD_REQUEST)
        
#         # Get payment record
#         try:
#             payment = Payment.objects.get(
#                 razorpay_order_id=razorpay_order_id,
#                 user=request.user
#             )
#         except Payment.DoesNotExist:
#             return Response({
#                 'success': False,
#                 'error': 'Payment not found'
#             }, status=status.HTTP_404_NOT_FOUND)
        
#         # Update payment
#         payment.razorpay_payment_id = razorpay_payment_id
#         payment.razorpay_signature = razorpay_signature
#         payment.status = 'success'
#         payment.completed_at = timezone.now()
#         payment.save()

#         # ========================================
#         # NEW: SEND RECEIPT EMAIL
#         # ========================================
#         try:
#             from .receipt.email_tasks import send_payment_receipt_email
#             logger.info(f"Queuing payment receipt email for payment {payment.id}")
#             send_payment_receipt_email.delay(str(payment.id))
#         except Exception as email_error:
#             logger.error(f"Failed to queue receipt email: {str(email_error)}")
        
#         # ========================================
#         # ADD TOKENS TO USER'S SUBSCRIPTION
#         # ========================================
#         try:
#             subscription = UserSubscription.objects.select_for_update().select_related('plan').get(user=request.user)
#             previous_bonus = subscription.bonus_tokens
#             previous_total = subscription.tokens_remaining + previous_bonus
            
#             # ADD tokens to bonus balance
#             subscription.bonus_tokens += payment.tokens_purchased
#             subscription.save()
            
#             new_total = subscription.tokens_remaining + subscription.bonus_tokens
            
#             print(f"💰 Token top-up: {previous_total} → {new_total} (+{payment.tokens_purchased})")
            
#             # Record token usage (addition)
#             TokenUsage.objects.create(
#                 user=request.user,
#                 subscription=subscription,
#                 tokens_used=0,
#                 feature='token_purchase',
#                 tokens_requested=0,
#                 description=f"Purchased {payment.tokens_purchased} tokens",
#                 status='success',
#                 metadata={
#                     'payment_id': str(payment.id),
#                     'tokens_added': payment.tokens_purchased,
#                     'previous_balance': previous_total,
#                     'new_balance': new_total
#                 }
#             )
            
#             log_payment_event(
#                 'tokens.purchased',
#                 request.user,
#                 subscription_id=str(subscription.id),
#                 payment_id=str(payment.id),
#                 tokens=payment.tokens_purchased,
#                 amount=float(payment.amount),
#                 ip_address=get_client_ip(request),
#             )

#             # ✅ Return updated token data for real-time sync
#             return Response({
#                 'success': True,
#                 'message': 'Token purchase verified successfully',
#                 'tokens_added': payment.tokens_purchased,
#                 'previous_balance': previous_total,
#                 'new_balance': new_total,
#                 # ✅ Include subscription data for frontend sync
#                 'subscription': {
#                     'tokens_remaining': subscription.tokens_remaining,
#                     'bonus_tokens': subscription.bonus_tokens,
#                     'total_available': new_total
#                 },
#                 # ✅ Include user token info for navbar/UI updates
#                 'user_tokens': {
#                     'tokens_remaining': subscription.tokens_remaining,
#                     'bonus_tokens': subscription.bonus_tokens,
#                     'total_available': new_total,
#                     'daily_limit': subscription.plan.daily_token_limit,
#                     'monthly_credits': subscription.plan.monthly_token_credits
#                 }
#             })
            
#         except UserSubscription.DoesNotExist:
#             return Response({
#                 'success': False,
#                 'error': 'No active subscription found'
#             }, status=status.HTTP_404_NOT_FOUND)


# class TokenUsageHistoryView(APIView):
#     """
#     Get user's token usage history
#     """
#     permission_classes = [IsAuthenticated]
    
#     def get(self, request):
#         """List token usage records"""
#         # Get pagination params
#         page = int(request.query_params.get('page', 1))
#         limit = int(request.query_params.get('limit', 50))
#         offset = (page - 1) * limit
        
#         usage_records = TokenUsage.objects.filter(
#             user=request.user
#         ).select_related('subscription')[offset:offset + limit]
        
#         serializer = TokenUsageSerializer(usage_records, many=True)
        
#         # Get summary stats
#         subscription = getattr(request.user, 'subscription', None)
#         summary = {
#             'total_used': subscription.total_tokens_used if subscription else 0,
#             'used_this_month': subscription.tokens_used_this_month if subscription else 0,
#             'remaining': subscription.tokens_remaining if subscription else 0
#         }
        
#         return Response({
#             'success': True,
#             'usage': serializer.data,
#             'summary': summary,
#             'count': usage_records.count()
#         })


class CancelSubscriptionView(APIView):
    """
    Cancel user's subscription
    """
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        """Cancel subscription"""
        cancel_immediately = request.data.get('cancel_immediately', False)
        
        try:
            subscription = UserSubscription.objects.select_for_update().get(user=request.user)
        except UserSubscription.DoesNotExist:
            return Response({
                'success': False,
                'error': 'No active subscription'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if subscription.status not in ['active', 'trial']:
            return Response({
                'success': False,
                'error': f'Subscription is already {subscription.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Cancel in Razorpay if subscription ID exists
        if subscription.razorpay_subscription_id:
            razorpay_service = RazorpayService()
            result = razorpay_service.cancel_subscription(
                subscription.razorpay_subscription_id,
                cancel_at_cycle_end=not cancel_immediately
            )
            
            if not result['success']:
                return Response({
                    'success': False,
                    'error': 'Failed to cancel subscription in payment gateway'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Update subscription
        if cancel_immediately:
            subscription.status = 'cancelled'
            subscription.cancelled_at = timezone.now()
        else:
            subscription.auto_renew = False
        
        subscription.save()
        
        log_payment_event(
            'subscription.cancelled',
            request.user,
            subscription_id=str(subscription.id),
            plan=subscription.plan.display_name,
            ip_address=get_client_ip(request),
        )

        return Response({
            'success': True,
            'message': 'Subscription cancelled successfully',
            'cancel_immediately': cancel_immediately
        })


@method_decorator(csrf_exempt, name='dispatch')
class RazorpayWebhookView(APIView):
    """Handle Razorpay webhooks"""
    permission_classes = [AllowAny]
    throttle_classes = [WebhookThrottle]
    
    def post(self, request):
        """Process webhook event"""
        try:
            # Get webhook signature and body
            webhook_signature = request.headers.get('X-Razorpay-Signature')
            webhook_body = request.body.decode('utf-8')
            
            logger.info(f"Received webhook, signature: {webhook_signature[:20]}...")
            
            if not webhook_signature:
                logger.error("No webhook signature in headers")
                return Response({
                    'success': False,
                    'error': 'No signature provided'
                }, status=400)
            
            # Parse webhook data BEFORE verification
            webhook_data = json.loads(webhook_body)
            event_type = webhook_data.get('event', 'unknown')
            event_id = webhook_data.get('event_id', '')
            
            logger.info(f"Event: {event_type}, ID: {event_id}")
            
            # Verify webhook signature before touching the database
            razorpay_service = RazorpayService()
            is_valid = razorpay_service.verify_webhook_signature(
                webhook_body,
                webhook_signature
            )
            
            if not is_valid:
                logger.error("Invalid webhook signature")
                return Response({
                    'success': False,
                    'error': 'Invalid signature'
                }, status=400)
            
            # Generate a unique event_id if Razorpay didn't send one
            if not event_id:
                event_id = f"evt_{timezone.now().timestamp()}"

            # ==========================================
            # 🔒 STRICT IDEMPOTENCY CHECK WITH DB LOCK
            # ==========================================
            with transaction.atomic():
                # Lock the row if it exists, or create it if it doesn't.
                webhook_log, created = WebhookLog.objects.select_for_update().get_or_create(
                    event_id=event_id,
                    defaults={
                        'event_type': event_type,
                        'payload': webhook_data,
                        'processed': False
                    }
                )

                if not created and webhook_log.processed:
                    logger.info(
                        f"Webhook {event_id} already processed at {webhook_log.processed_at}. "
                        f"Returning 200 to stop Razorpay retries."
                    )
                    return Response({
                        'success': True,
                        'message': 'Already processed',
                        'original_processed_at': webhook_log.processed_at.isoformat() if webhook_log.processed_at else None
                    }, status=200)

                logger.info(f"Webhook log acquired and processing: {webhook_log.id}")
            
            # Process based on event type
            payload = webhook_data.get('payload', {})
            
            try:
                if event_type == 'payment.captured':
                    self._handle_payment_captured(payload, webhook_log)
                elif event_type == 'payment.failed':
                    self._handle_payment_failed(payload, webhook_log)
                elif event_type == 'subscription.activated':
                    self._handle_subscription_activated(payload, webhook_log)
                elif event_type == 'subscription.charged':
                    self._handle_subscription_charged(payload, webhook_log)
                elif event_type == 'subscription.cancelled':
                    self._handle_subscription_cancelled(payload, webhook_log)
                else:
                    logger.warning(f"️ Unhandled event type: {event_type}")
                
                # Mark as processed
                webhook_log.processed = True
                webhook_log.processed_at = timezone.now()
                webhook_log.save()
                
                logger.info(f"Webhook processed successfully: {event_type}")
                
                return Response({'success': True})
                
            except Exception as e:
                logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
                # We need to fetch the log object again because we might be outside the atomic block
                # depending on how inner functions handle transactions, but setting error is fine here.
                webhook_log.processing_error = str(e)
                webhook_log.save(update_fields=['processing_error'])
                
                # CRITICAL: Return 500 error to force Razorpay to retry the webhook later
                return Response({
                    'success': False,
                    'error': 'Internal processing error, please retry'
                }, status=500)
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in webhook: {str(e)}")
            return Response({
                'success': False,
                'error': 'Invalid JSON'
            }, status=400)
            
        except Exception as e:
            logger.error(f"Unexpected error in webhook: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=500)
    def _handle_payment_captured(self, payload, webhook_log):
        """Handle successful payment - UPDATED FOR FULL RELIABILITY"""
        payment_entity = payload.get('payment', {}).get('entity', {})
        order_id = payment_entity.get('order_id')
        payment_id = payment_entity.get('id')
        
        logger.info(f"Payment captured webhook: {payment_id} for order: {order_id}")
        
        if order_id:
            payment = Payment.objects.filter(razorpay_order_id=order_id).first()
            if payment:
                if payment.status != 'success':
                    # Payment hasn't been verified by frontend yet, activate it via webhook background job!
                    success, result, updated_payment = VerifyPaymentView.process_successful_payment(
                        payment, payment_id, None, None
                    )
                    if success:
                        logger.info(f"✅ Subscription directly activated via webhook for payment {payment.id}")
                    else:
                        logger.error(f"Failed to activate subscription via webhook: {result}")
                else:
                    logger.info("Payment already correctly marked as success by frontend. Webhook skipping activation.")
                    
                # Link webhook log to payment in either case
                webhook_log.payment = payment
                webhook_log.user = payment.user
                webhook_log.save()

    
    def _handle_payment_failed(self, payload, webhook_log):
        """Handle failed payment - UPDATED"""
        from datetime import timedelta
        
        payment_entity = payload.get('payment', {}).get('entity', {})
        order_id = payment_entity.get('order_id')
        payment_id = payment_entity.get('id')
        error_desc = payment_entity.get('error_description', 'Payment failed')
        error_code = payment_entity.get('error_code', 'UNKNOWN')
        
        logger.info(f"Payment failed for order: {order_id}")
        
        if order_id:
            payments = Payment.objects.filter(razorpay_order_id=order_id)
            updated = payments.update(
                razorpay_payment_id=payment_id,  # ✅ Save payment ID even on failure
                status='failed',
                failure_reason=f"{error_code}: {error_desc}"
            )
            logger.info(f"Updated {updated} payment records as failed")
            
            # Update subscription's payment status and set grace period
            payment = payments.first()
            if payment and payment.subscription:
                subscription = payment.subscription
                subscription.last_payment_status = 'failed'
                subscription.failed_payment_count += 1
                
                subscription.save(update_fields=[
                    'last_payment_status',
                    'failed_payment_count'
                ])
            
            # Link webhook log to payment
            if payment:
                webhook_log.payment = payment
                webhook_log.user = payment.user
                webhook_log.save()
            
            # ✅ Send failure email notification
            if payment:
                try:
                    send_payment_failure_email.delay(str(payment.id))
                    logger.info(f"Queued payment failure email for payment {payment.id}")
                except Exception as email_error:
                    logger.error(f"Failed to queue failure email: {str(email_error)}")
                # Don't fail the webhook if email queuing fails
            
            if payment:
                log_payment_event(
                    'webhook.payment_failed',
                    payment.user,
                    payment_id=str(payment.id),
                    amount=float(payment.amount),
                    details={'failure_reason': payment.failure_reason}
                )
            









    
    def _handle_subscription_activated(self, payload, webhook_log):
        """Handle subscription activation"""
        try:
            sub_entity = payload.get('subscription', {}).get('entity', {})
            sub_id = sub_entity.get('id')
            
            logger.info(f"Subscription activated: {sub_id}")
            
            if sub_id:
                subs = UserSubscription.objects.filter(razorpay_subscription_id=sub_id)
                updated = subs.update(status='active')
                
                if updated > 0:
                    sub = subs.first()
                    log_payment_event(
                        'webhook.subscription.activated',
                        sub.user,
                        subscription_id=str(sub.id),
                        plan=sub.plan.display_name
                    )
                
        except Exception as e:
            logger.error(f"Error in _handle_subscription_activated: {str(e)}")
            raise
    
    def _handle_subscription_charged(self, payload, webhook_log):
        """Handle subscription charge"""
        try:
            payment_entity = payload.get('payment', {}).get('entity', {})
            logger.info(f"Subscription charged: {payment_entity.get('id')}")
            
        except Exception as e:
            logger.error(f"Error in _handle_subscription_charged: {str(e)}")
            raise
    
    def _handle_subscription_cancelled(self, payload, webhook_log):
        """Handle subscription cancellation"""
        try:
            sub_entity = payload.get('subscription', {}).get('entity', {})
            sub_id = sub_entity.get('id')
            
            logger.info(f"Subscription cancelled: {sub_id}")
            
            if sub_id:
                subs = UserSubscription.objects.filter(razorpay_subscription_id=sub_id)
                updated = subs.update(
                    status='cancelled',
                    cancelled_at=timezone.now()
                )

                if updated > 0:
                    sub = subs.first()
                    log_payment_event(
                        'webhook.subscription.cancelled',
                        sub.user,
                        subscription_id=str(sub.id),
                        plan=sub.plan.display_name
                    )
                
        except Exception as e:
            logger.error(f"Error in _handle_subscription_cancelled: {str(e)}")
            raise


class PaymentHistoryView(APIView):
    """
    Get user's payment history
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List payment records"""
        payments = Payment.objects.filter(user=request.user).order_by('-created_at')
        serializer = PaymentSerializer(payments, many=True)
        
        return Response({
            'success': True,
            'payments': serializer.data
        })
    

# payments/views.py

# class AutoRefillSettingsView(APIView):
#     """Manage auto-refill settings"""
#     permission_classes = [IsAuthenticated]
    
#     def get(self, request):
#         """Get current auto-refill settings"""
#         try:
#             subscription = UserSubscription.objects.get(user=request.user)
#             return Response({
#                 'success': True,
#                 'auto_refill_enabled': subscription.auto_refill_enabled,
#                 'auto_refill_threshold': subscription.auto_refill_threshold,
#                 'auto_refill_package': {
#                     'id': str(subscription.auto_refill_package.id),
#                     'name': subscription.auto_refill_package.name,
#                     'tokens': subscription.auto_refill_package.get_total_tokens()
#                 } if subscription.auto_refill_package else None
#             })
#         except UserSubscription.DoesNotExist:
#             return Response({
#                 'success': False,
#                 'error': 'No subscription found'
#             }, status=404)
    
#     def post(self, request):
#         """Update auto-refill settings"""
#         try:
#             subscription = UserSubscription.objects.get(user=request.user)
            
#             subscription.auto_refill_enabled = request.data.get(
#                 'enabled',
#                 subscription.auto_refill_enabled
#             )
#             subscription.auto_refill_threshold = request.data.get(
#                 'threshold',
#                 subscription.auto_refill_threshold
#             )
            
#             package_id = request.data.get('package_id')
#             if package_id:
#                 package = TokenPackage.objects.get(id=package_id)
#                 subscription.auto_refill_package = package
            
#             subscription.save()
            
#             return Response({
#                 'success': True,
#                 'message': 'Auto-refill settings updated'
#             })
            
#         except UserSubscription.DoesNotExist:
#             return Response({
#                 'success': False,
#                 'error': 'No subscription found'
#             }, status=404)
#         except TokenPackage.DoesNotExist:
#             return Response({
#                 'success': False,
#                 'error': 'Invalid package'
#             }, status=404)

# payments/views.py
from django.utils import timezone


class PaymentMethodsView(APIView):
    """Manage payment methods - Fetch details from Razorpay"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List user's payment methods"""
        methods = PaymentMethod.objects.filter(user=request.user, is_active=True)
        serializer = PaymentMethodSerializer(methods, many=True)
        return Response({
            'success': True,
            'payment_methods': serializer.data
        })
    
    def post(self, request):
        """
        Add new payment method from Razorpay payment
        
        Expected data:
        {
            "razorpay_payment_id": "pay_xxxxx",
            "is_default": false
        }
        """
        try:
            # Get payment ID from request
            payment_id = request.data.get('razorpay_payment_id')
            is_default = request.data.get('is_default', False)
            
            if not payment_id:
                return Response({
                    'success': False,
                    'error': 'razorpay_payment_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if payment method already exists
            if PaymentMethod.objects.filter(razorpay_payment_id=payment_id).exists():
                return Response({
                    'success': False,
                    'error': 'Payment method already saved'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Fetch payment details from Razorpay
            razorpay_service = RazorpayService()
            payment_data = razorpay_service.fetch_payment_details(payment_id)
            
            if not payment_data.get('success'):
                logger.error(f"Failed to fetch payment {payment_id}: {payment_data.get('error')}")
                return Response({
                    'success': False,
                    'error': 'Failed to fetch payment details from Razorpay'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify payment was successful
            if payment_data.get('status') != 'captured':
                return Response({
                    'success': False,
                    'error': f"Payment is {payment_data.get('status')}, not captured"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            method_type = payment_data.get('method_type')
            
            # Prepare common fields
            payment_method_data = {
                'user': request.user,
                'razorpay_payment_id': payment_id,
                'method_type': method_type,
                'email': payment_data.get('email', ''),
                'contact': payment_data.get('contact', ''),
                'is_default': is_default,
            }
            
            # Add method-specific fields
            if method_type == 'card':
                payment_method_data.update({
                    'last4': payment_data.get('last4', ''),
                    'card_network': payment_data.get('card_network', ''),
                    'card_issuer': payment_data.get('card_issuer', ''),
                    'card_type': payment_data.get('card_type', ''),
                })
            
            elif method_type == 'upi':
                payment_method_data.update({
                    'upi_vpa': payment_data.get('upi_vpa', ''),
                })
            
            elif method_type == 'netbanking':
                payment_method_data.update({
                    'bank_name': payment_data.get('bank_name', ''),
                })
            
            elif method_type == 'wallet':
                payment_method_data.update({
                    'wallet_name': payment_data.get('wallet_name', ''),
                })
            
            # Create payment method
            method = PaymentMethod.objects.create(**payment_method_data)
            
            logger.info(f"Payment method created for user {request.user.id}: {method.id} ({method_type})")
            
            return Response({
                'success': True,
                'message': 'Payment method saved successfully',
                'payment_method': PaymentMethodSerializer(method).data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating payment method: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'Failed to save payment method'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, method_id):
        """Remove payment method (soft delete)"""
        try:
            method = PaymentMethod.objects.get(
                id=method_id,
                user=request.user
            )
            
            # Soft delete by marking as inactive
            method.is_active = False
            method.save()
            
            logger.info(f"Payment method {method_id} deactivated for user {request.user.id}")
            
            return Response({
                'success': True,
                'message': 'Payment method removed successfully'
            })
            
        except PaymentMethod.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Payment method not found'
            }, status=status.HTTP_404_NOT_FOUND)

class UpgradePlanView(APIView):
    """
    Upgrade/downgrade subscription plan with proper business logic
    UPDATED: Now blocks mid-cycle downgrades and enforces all rules
    """
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        """Upgrade or downgrade plan with validation"""
        new_plan_id = request.data.get('plan_id')
        new_billing_cycle = request.data.get('billing_cycle', 'monthly')
        force_immediate = request.data.get('force_immediate', False)  # For admin override
        token_loss_confirmed = request.data.get('token_loss_confirmed', False)
        
        # Validate inputs
        if not new_plan_id:
            return Response({
                'success': False,
                'error': 'plan_id is required'
            }, status=400)
        
        # Get current subscription
        try:
            current_subscription = UserSubscription.objects.select_for_update().select_related('plan').get(
                user=request.user
            )
        except UserSubscription.DoesNotExist:
            return Response({
                'success': False,
                'error': 'No active subscription found'
            }, status=404)
        
        # Get new plan
        try:
            new_plan = SubscriptionPlan.objects.get(id=new_plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Invalid or inactive plan'
            }, status=404)
        
        # Check if same plan
        if current_subscription.plan.id == new_plan.id and current_subscription.billing_cycle == new_billing_cycle:
            return Response({
                'success': False,
                'error': 'You are already on this plan'
            }, status=400)
        
        # Check if plan allows self-service changes
        if not new_plan.allow_self_service_changes:
            return Response({
                'success': False,
                'error': f'{new_plan.display_name} plan requires admin approval. Please contact support.',
                'contact_support': True
            }, status=403)
        
        # Check if user can change plan
        can_change, reason, is_upgrade = current_subscription.can_change_plan(
            new_plan, 
            new_billing_cycle
        )
        
        if not can_change and not force_immediate:
            # Determine if this is a downgrade that can be scheduled
            days_until_renewal = (current_subscription.current_period_end - timezone.now()).days
            
            if "Downgrades are only allowed at renewal" in reason:
                # Offer to schedule the downgrade
                return Response({
                    'success': False,
                    'error': reason,
                    'code': 'DOWNGRADE_NOT_ALLOWED_MID_CYCLE',
                    'can_schedule': True,
                    'renewal_date': current_subscription.current_period_end.isoformat(),
                    'days_until_renewal': days_until_renewal,
                    'suggestion': 'You can schedule this plan change to take effect at your next renewal'
                }, status=400)
            else:
                # Other blocking reasons (payment failed, commitment, etc.)
                return Response({
                    'success': False,
                    'error': reason,
                    'can_schedule': False
                }, status=403)
        
        # Check for token loss (only for downgrades)
        if not is_upgrade:
            will_lose_tokens, tokens_to_lose = current_subscription.check_token_loss(new_plan)
            
            if will_lose_tokens and not token_loss_confirmed:
                return Response({
                    'success': False,
                    'warning': True,
                    'code': 'TOKEN_LOSS_WARNING',
                    'message': f'Switching to {new_plan.display_name} will result in loss of {tokens_to_lose} unused tokens',
                    'tokens_to_lose': tokens_to_lose,
                    'current_tokens': current_subscription.tokens_remaining,
                    'new_plan_tokens': new_plan.monthly_token_credits,
                    'confirmation_required': True
                }, status=200)
        
        # UPGRADE PATH (Immediate with proration)
        if is_upgrade:
            return self._handle_upgrade(
                request.user,
                current_subscription,
                new_plan,
                new_billing_cycle
            )
        
        # DOWNGRADE PATH (Scheduled for renewal)
        else:
            return self._handle_downgrade(
                current_subscription,
                new_plan,
                new_billing_cycle
            )
    
    def _handle_upgrade(self, user, current_subscription, new_plan, new_billing_cycle):
        """Handle immediate upgrade with proration"""
        from .utils import calculate_proration
        from .razorpay_service import RazorpayService
        from datetime import datetime
        
        # Calculate proration
        proration = calculate_proration(
            current_subscription,
            new_plan,
            new_billing_cycle
        )
        
        # Create payment for prorated amount
        if proration['prorated_amount_usd'] > 0:
            short_receipt = f'upg{int(datetime.now().timestamp())}'
            razorpay_service = RazorpayService()
            order_result = razorpay_service.create_order(
            amount=proration['prorated_amount_usd'],
            currency='USD',
            receipt=short_receipt,
            notes={
                'user_id': str(user.id),
                'new_plan_id': str(new_plan.id),
                'change_type': 'upgrade',
                'proration': str(proration['prorated_amount_usd'])
            }
        )
            
            if not order_result['success']:
                return Response({
                    'success': False,
                    'error': 'Failed to create payment order'
                }, status=500)
            
            # Return payment details for frontend
            return Response({
                'success': True,
                'requires_payment': True,
                'order_id': order_result['order']['id'],
                'amount': float(proration['prorated_amount_usd']),
                'currency': 'USD',
                'proration_details': proration,
                'new_plan': {
                    'id': str(new_plan.id),
                    'name': new_plan.display_name,
                    'billing_cycle': new_billing_cycle
                }
            })
        else:
            # Free upgrade or proration handled
            previous_tokens = current_subscription.tokens_remaining
            previous_bonus = current_subscription.bonus_tokens
            
            # ✅ ADD new plan tokens to existing balance
            current_subscription.plan = new_plan
            current_subscription.billing_cycle = new_billing_cycle
            current_subscription.tokens_remaining = previous_tokens + new_plan.monthly_token_credits  # ✅ ADD tokens
            current_subscription.bonus_tokens = previous_bonus  # ✅ PRESERVE bonus
            current_subscription.save()
            
            print(f"✅ Plan upgraded: {previous_tokens} + {new_plan.monthly_token_credits} = {current_subscription.tokens_remaining}")
            
            log_payment_event(
                'subscription.upgraded',
                user,
                subscription_id=str(current_subscription.id),
                plan=new_plan.display_name,
                tokens=current_subscription.tokens_remaining,
                ip_address=get_client_ip(self.request),
            )
            
            # Create payment record with token details
            Payment.objects.create(
                user=user,
                subscription=current_subscription,
                payment_type='upgrade',
                amount=0,
                currency='INR',
                status='success',
                completed_at=timezone.now(),
                metadata={
                    'plan_id': str(new_plan.id),
                    'billing_cycle': new_billing_cycle,
                    'change_type': 'free_upgrade',
                    'previous_tokens': previous_tokens,
                    'tokens_added': new_plan.monthly_token_credits,
                    'new_balance': current_subscription.tokens_remaining
                }
            )
            
            return Response({
                'success': True,
                'requires_payment': False,
                'message': 'Plan upgraded successfully',
                'new_plan': {
                    'name': new_plan.display_name,
                    'billing_cycle': new_billing_cycle
                }
            })
    
    def _handle_downgrade(self, current_subscription, new_plan, new_billing_cycle):
        """Handle scheduled downgrade (at renewal)"""
        
        # Schedule the plan change
        current_subscription.schedule_plan_change(
            new_plan,
            new_billing_cycle,
            reason=f"User-initiated downgrade from {current_subscription.plan.display_name}"
        )
        
        # Disable auto-renew to prevent charging for current plan
        current_subscription.auto_renew = False
        current_subscription.save()

        log_payment_event(
            'subscription.downgraded',
            self.request.user,
            subscription_id=str(current_subscription.id),
            plan=new_plan.display_name,
            ip_address=get_client_ip(self.request),
            details={'current_plan': current_subscription.plan.display_name},
        )
        
        days_until_change = (current_subscription.current_period_end - timezone.now()).days
        
        return Response({
            'success': True,
            'requires_payment': False,
            'scheduled': True,
            'message': f'Plan change scheduled successfully',
            'effective_date': current_subscription.current_period_end.isoformat(),
            'days_until_change': days_until_change,
            'current_plan': {
                'name': current_subscription.plan.display_name,
                'billing_cycle': current_subscription.billing_cycle
            },
            'new_plan': {
                'name': new_plan.display_name,
                'billing_cycle': new_billing_cycle
            },
            'note': f'Your plan will change to {new_plan.display_name} on {current_subscription.current_period_end.date()}'
        })


class CancelScheduledChangeView(APIView):
    """Cancel a scheduled plan change"""
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        """Cancel scheduled plan change"""
        try:
            subscription = UserSubscription.objects.select_for_update().get(user=request.user)
        except UserSubscription.DoesNotExist:
            return Response({
                'success': False,
                'error': 'No subscription found'
            }, status=404)
        
        if not subscription.scheduled_plan:
            return Response({
                'success': False,
                'error': 'No scheduled plan change found'
            }, status=400)
        
        old_scheduled_plan = subscription.scheduled_plan.display_name
        
        # Clear scheduled change
        subscription.scheduled_plan = None
        subscription.scheduled_billing_cycle = None
        subscription.scheduled_change_reason = None
        subscription.auto_renew = True  # Re-enable auto-renew
        subscription.save()
        
        return Response({
            'success': True,
            'message': f'Cancelled scheduled change to {old_scheduled_plan}',
            'current_plan': subscription.plan.display_name
        })


class GetPlanChangePreviewView(APIView):
    """Preview what would happen if user changes plan"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Get preview of plan change"""
        new_plan_id = request.data.get('plan_id')
        new_billing_cycle = request.data.get('billing_cycle', 'monthly')
        
        try:
            new_plan = SubscriptionPlan.objects.get(id=new_plan_id)
        except SubscriptionPlan.DoesNotExist:
            return Response({'success': False, 'error': 'Invalid plan'}, status=404)
        
        try:
            current_subscription = UserSubscription.objects.select_related('plan').get(
                user=request.user
            )
            # Check if can change
            can_change, reason, is_upgrade = current_subscription.can_change_plan(
                new_plan,
                new_billing_cycle
            )
            # Check token loss
            will_lose_tokens, tokens_to_lose = current_subscription.check_token_loss(new_plan)
            days_until_renewal = (current_subscription.current_period_end - timezone.now()).days
            renewal_date = current_subscription.current_period_end.isoformat()
            scheduled_change_available = not is_upgrade
            current_tokens = getattr(current_subscription, 'tokens_remaining', 0)
            
            # Calculate proration for upgrades
            proration = None
            if is_upgrade:
                from .utils import calculate_proration
                proration = calculate_proration(
                    current_subscription,
                    new_plan,
                    new_billing_cycle
                )
                base_usd = float(proration['prorated_amount_usd'])
            else:
                base_usd = float(new_plan.annual_price if new_billing_cycle == 'annual' else new_plan.monthly_price)
                
            current_plan_data = {
                'name': current_subscription.plan.display_name,
                'price': float(current_subscription.plan.monthly_price),
                'billing_cycle': current_subscription.billing_cycle
            }
                
        except UserSubscription.DoesNotExist:
            # User has no subscription yet (initial purchase)
            can_change = True
            reason = ""
            is_upgrade = True
            will_lose_tokens = False
            tokens_to_lose = 0
            current_tokens = 0
            days_until_renewal = 0
            renewal_date = (timezone.now() + timezone.timedelta(days=30)).isoformat()
            scheduled_change_available = False
            current_plan_data = None
            proration = None
            base_usd = float(new_plan.annual_price if new_billing_cycle == 'annual' else new_plan.monthly_price)
            
        local_total = float(new_plan.annual_price if new_billing_cycle == 'annual' else new_plan.monthly_price)
        currency = 'USD'
        
        # Calculate local pricing and taxes
        from accounts.session_tracker import SessionTracker
        from payments.currency_service import CurrencyService
        from .utils import calculate_tax

        ip_address, _ = SessionTracker.get_client_ip(request)
        geo_data = SessionTracker.get_geolocation(ip_address)
        country_code = geo_data.get('country_code', 'US')
        if country_code == 'LOCAL':
            country_code = 'IN'
        
        # Convert to local currency
        currency_service = CurrencyService()
        payment_details = currency_service.get_payment_details(Decimal(str(base_usd)), country_code)
        
        # Calculate tax on local amount
        tax_details = calculate_tax(payment_details['local_amount'], country_code)
        
        new_plan_tokens = new_plan.features.get('dms_per_month', 0)
        
        return Response({
            'success': True,
            'can_change_immediately': can_change,
            'reason': reason,
            'is_upgrade': is_upgrade,
            'change_type': 'upgrade' if is_upgrade else 'downgrade',
            'will_lose_tokens': will_lose_tokens,
            'tokens_to_lose': tokens_to_lose,
            'current_tokens': current_tokens,
            'new_plan_tokens': new_plan_tokens,
            'proration': proration,
            'currency_details': {
                'local_currency': payment_details['local_currency'],
                'exchange_rate': float(payment_details['exchange_rate']),
                'local_amount_pre_tax': float(payment_details['local_amount']),
                'base_usd_amount': float(base_usd),
                'tax_rate': float(tax_details['tax_rate']),
                'tax_name': tax_details['tax_name'],
                'tax_amount': float(tax_details['tax_amount']),
                'final_local_amount': float(tax_details['total_amount'])
            },
            'location_detected': country_code,
            'days_until_renewal': days_until_renewal,
            'renewal_date': renewal_date,
            'scheduled_change_available': scheduled_change_available,
            'current_plan': current_plan_data,
            'new_plan': {
                'name': new_plan.display_name,
                'price': float(new_plan.monthly_price if new_billing_cycle == 'monthly' else new_plan.annual_price),
                'billing_cycle': new_billing_cycle
            }
        })


class ReferralCodeView(APIView):
    """Get or create user's referral code"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user's referral code"""
        code, created = ReferralCode.objects.get_or_create(
            user=request.user,
            defaults={'code': ReferralCode.generate_code(request.user.username)}
        )
        
        return Response({
            'success': True,
            'referral_code': code.code,
            'stats': {
                'total_referrals': code.total_referrals,
                'total_earned_tokens': code.total_earned_tokens,
                'referrer_bonus': code.referrer_bonus_tokens,
                'referee_bonus': code.referee_bonus_tokens
            }
        })


class ReferralStatsView(APIView):
    """Get user's referral statistics"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get referral stats for authenticated user"""
        try:
            # Get user's referral code
            referral_code = ReferralCode.objects.get(user=request.user)

            # Get successful referrals (where referee has a subscription)
            successful_referrals = Referral.objects.filter(
                referrer=request.user,
                referee__subscription__isnull=False
            ).count()

            # Get pending referrals (referee signed up but no subscription yet)
            pending_referrals = Referral.objects.filter(
                referrer=request.user
            ).exclude(
                referee__subscription__isnull=False
            ).count()

            return Response({
                'success': True,
                'stats': {
                    'total_referrals': referral_code.total_referrals,
                    'successful_referrals': successful_referrals,
                    'pending_referrals': pending_referrals,
                    'total_earned_tokens': referral_code.total_earned_tokens
                }
            })

        except ReferralCode.DoesNotExist:
            # User doesn't have a referral code yet, return zeros
            return Response({
                'success': True,
                'stats': {
                    'total_referrals': 0,
                    'successful_referrals': 0,
                    'pending_referrals': 0,
                    'total_earned_tokens': 0
                }
            })


class ApplyReferralCodeView(APIView):
    """Apply referral code during signup"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Apply referral code"""
        code = request.data.get('referral_code')

        # Check if user already used a referral
        if hasattr(request.user, 'referred_by'):
            return Response({
                'success': False,
                'error': 'You have already used a referral code'
            }, status=400)

        try:
            referral_code = ReferralCode.objects.get(code=code)

            # Can't refer yourself
            if referral_code.user == request.user:
                return Response({
                    'success': False,
                    'error': 'Cannot use your own referral code'
                }, status=400)

            # Create referral
            referral = Referral.objects.create(
                referrer=referral_code.user,
                referee=request.user,
                referral_code=referral_code
            )

            return Response({
                'success': True,
                'message': f'Referral code applied! You will receive {referral_code.referee_bonus_tokens} bonus tokens when you subscribe.',
                'bonus_tokens': referral_code.referee_bonus_tokens
            })

        except ReferralCode.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Invalid referral code'
            }, status=404)

# payments/views.py

class PaymentAnalyticsView(APIView):
    """Get payment and usage analytics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get comprehensive analytics"""
        from django.db.models import Sum, Count, Avg
        from django.db.models.functions import TruncDate
        
        # Get date range
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        # Payment stats
        payment_stats = Payment.objects.filter(
            user=request.user,
            created_at__gte=start_date,
            status='success'
        ).aggregate(
            total_spent=Sum('amount'),
            payment_count=Count('id'),
            avg_payment=Avg('amount')
        )
        
        # # Token usage stats
        # usage_stats = TokenUsage.objects.filter(
        #     user=request.user,
        #     created_at__gte=start_date
        # ).aggregate(
        #     total_tokens=Sum('tokens_used'),
        #     usage_count=Count('id'),
        #     avg_tokens_per_use=Avg('tokens_used')
        # )
        
        # # Daily usage trend
        # daily_usage = TokenUsage.objects.filter(
        #     user=request.user,
        #     created_at__gte=start_date
        # ).annotate(
        #     date=TruncDate('created_at')
        # ).values('date').annotate(
        #     tokens=Sum('tokens_used'),
        #     count=Count('id')
        # ).order_by('date')
        
        # # Feature breakdown
        # feature_breakdown = TokenUsage.objects.filter(
        #     user=request.user,
        #     created_at__gte=start_date
        # ).values('feature').annotate(
        #     tokens=Sum('tokens_used'),
        #     count=Count('id')
        # ).order_by('-tokens')
        
        return Response({
            'success': True,
            'period_days': days,
            'payment_stats': {
                'total_spent': float(payment_stats['total_spent'] or 0),
                'payment_count': payment_stats['payment_count'],
                'average_payment': float(payment_stats['avg_payment'] or 0)
            }
            # 'usage_stats': {
            #     'total_tokens': usage_stats['total_tokens'] or 0,
            #     'usage_count': usage_stats['usage_count'],
            #     'average_per_use': float(usage_stats['avg_tokens_per_use'] or 0)
            # },
            # 'daily_trend': list(daily_usage),
            # 'feature_breakdown': list(feature_breakdown)
        })
    





class GenerateTestSignatureView(APIView):
    """
    DEBUG-ONLY: Generate valid Razorpay payment signature for Postman testing.
    
    🔒 SECURITY:
    - Gated behind DEBUG in urls.py (primary protection)
    - Returns 404 if DEBUG=False (defense-in-depth)
    - Requires authentication even in DEBUG mode
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 🔒 Defense-in-depth: refuse to run in production
        if not settings.DEBUG:
            return Response(status=404)

        order_id = request.data.get('razorpay_order_id')
        payment_id = request.data.get('razorpay_payment_id', 'pay_test_manual')

        if not order_id:
            return Response({
                'success': False,
                'error': 'razorpay_order_id is required'
            }, status=400)

        from .razorpay_service import RazorpayService
        razorpay_service = RazorpayService()

        signature = hmac.new(
            razorpay_service.key_secret.encode('utf-8'),
            f"{order_id}|{payment_id}".encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return Response({
            'success': True,
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'signature': signature,
            'message': 'Use these values in /verify/ endpoint'
        })
    
class GenerateWebhookSignatureView(APIView):
    """
    DEBUG-ONLY: Generate valid Razorpay webhook signature for testing.
    
    🔒 SECURITY:
    - Gated behind DEBUG in urls.py (primary protection)
    - Returns 404 if DEBUG=False (defense-in-depth)
    - Now requires authentication (was previously open to anyone)
    - No longer returns the webhook_secret in response
    """
    permission_classes = [IsAuthenticated]  # 🔒 Was [] — now requires auth even in DEBUG

    def post(self, request):
        # 🔒 Defense-in-depth: refuse to run in production
        if not settings.DEBUG:
            return Response(status=404)

        payload = request.data

        if not payload:
            return Response({
                'success': False,
                'error': 'Request body (webhook payload) is required'
            }, status=400)

        from .razorpay_service import RazorpayService
        razorpay_service = RazorpayService()

        import json
        payload_string = json.dumps(payload)

        signature = hmac.new(
            razorpay_service.webhook_secret.encode('utf-8'),
            payload_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return Response({
            'success': True,
            'signature': signature,
            # 🔒 REMOVED: 'webhook_secret' was previously leaked here
            'payload': payload,
            'message': 'Use the signature in X-Razorpay-Signature header'
        })

    

class GetCurrencyConversionView(APIView):
    """
    Get currency conversion details for user's location
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Convert USD amount to user's local currency
        
        Request body:
        {
            "amount_usd": 25.00,
            "country_code": "IN"  # Optional, will detect from IP
        }
        """
        try:
            amount_usd = Decimal(str(request.data.get('amount_usd', 0)))
            country_code = request.data.get('country_code')
            
            # If no country code, detect from IP
            if not country_code:
                from accounts.session_tracker import SessionTracker
                ip_address, _ = SessionTracker.get_client_ip(request)
                geo_data = SessionTracker.get_geolocation(ip_address)
                country_code = geo_data.get('country_code', 'US')
            
            # Get conversion details
            currency_service = CurrencyService()
            conversion_details = currency_service.get_payment_details(
                amount_usd,
                country_code
            )
            
            return Response({
                'success': True,
                **conversion_details
            })
            
        except Exception as e:
            logger.error(f"Currency conversion error: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

# class UserTokenBalanceRealtimeView(APIView):
#     """
#     Get user's token balance in real-time (for polling or websocket use)
#     """
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         try:
#             subscription = UserSubscription.objects.select_related('plan').get(user=request.user)
#             total_available = subscription.tokens_remaining + subscription.bonus_tokens
#             total_allocation = subscription.plan.monthly_token_credits
#             percentage_remaining = (subscription.tokens_remaining / total_allocation) * 100 if total_allocation > 0 else 0

#             data = {
#                 'success': True,
#                 'tokens': {
#                     'total_available': total_available,
#                     'base_remaining': subscription.tokens_remaining,
#                     'bonus_tokens': subscription.bonus_tokens,
#                     'rollover_tokens': subscription.rollover_tokens,
#                     'used_today': subscription.tokens_used_today,
#                     'used_this_month': subscription.tokens_used_this_month,
#                     'total_used': subscription.total_tokens_used,
#                     'daily_limit': subscription.plan.daily_token_limit,
#                     'monthly_allocation': subscription.plan.monthly_token_credits,
#                     'percentage_remaining': round(percentage_remaining, 2)
#                 },
#                 'plan': {
#                     'name': subscription.plan.display_name,
#                     'billing_cycle': subscription.billing_cycle,
#                     'status': subscription.status
#                 },
#                 'usage': {
#                     'today': subscription.tokens_used_today,
#                     'this_month': subscription.tokens_used_this_month,
#                     'daily_limit': subscription.plan.daily_token_limit,
#                     'daily_remaining': max(0, subscription.plan.daily_token_limit - subscription.tokens_used_today)
#                 }
#             }
#             return Response(data)
#         except UserSubscription.DoesNotExist:
#             return Response({
#                 'success': True,
#                 'tokens': {
#                     'total_available': 0,
#                     'base_remaining': 0,
#                     'bonus_tokens': 0,
#                     'rollover_tokens': 0,
#                     'used_today': 0,
#                     'used_this_month': 0,
#                     'total_used': 0,
#                     'daily_limit': 0,
#                     'monthly_allocation': 0,
#                     'percentage_remaining': 0
#                 },
#                 'plan': {
#                     'name': 'No Active Plan',
#                     'billing_cycle': None,
#                     'status': 'inactive'
#                 },
#                 'usage': {
#                     'today': 0,
#                     'this_month': 0,
#                     'daily_limit': 0,
#                     'daily_remaining': 0
#                 },
#                 'message': 'No active subscription. Please subscribe to a plan.'
#             })



class DownloadInvoiceView(APIView):
    """
    Download a PDF invoice for a specific payment.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, payment_id):
        try:
            # Ensure the user can only download their own invoice
            payment = Payment.objects.get(id=payment_id, user=request.user)
            
            # Only allow downloading successful payments
            if payment.status != 'success':
                return Response({
                    'success': False,
                    'error': 'Invoice is only available for successful payments.'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            from .invoice_generator import generate_invoice_pdf
            pdf_bytes = generate_invoice_pdf(payment)
            
            # Check if generation returned an error message instead of PDF bytes
            if pdf_bytes and pdf_bytes.startswith(b"Error:"):
                return Response({
                    'success': False,
                    'error': pdf_bytes.decode('utf-8')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Return as a downloadable file
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            filename = f"Invoice_{payment.invoice_number or payment.id}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Payment.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Payment not found or access denied.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error generating invoice for payment {payment_id}: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': f'Failed to generate invoice: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)