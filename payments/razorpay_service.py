"""
Razorpay Service - UPDATED with customer fetch by email
"""
import razorpay
import hmac
import hashlib
import logging
from decimal import Decimal
from typing import Dict, Any
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)
class RazorpayService:
    """
    Service class for Razorpay payment gateway integration
    """
    
    def __init__(self):
        """Initialize Razorpay client"""
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self.webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
        self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
    
    def create_order(
    self,
    amount: Decimal,
    currency: str = 'USD',
    receipt: str = None,
    notes: Dict[str, Any] = None
) -> Dict[str, Any]:
        """Create Razorpay order"""
        try:
            # Convert to smallest currency unit (paise for USD)
            amount_in_cents = int(amount * 100)
            
            # ✅ ADD VALIDATION
            if amount_in_cents < 100:  # Minimum 1 USD = 100 cents
                return {
                    'success': False,
                    'error': f'Amount {amount_in_cents} cents (${amount}) is below minimum ($1.00)'
                }
            
            order_data = {
                'amount': amount_in_cents,
                'currency': currency,
                'receipt': receipt or f'order_{timezone.now().timestamp()}',
                'notes': notes or {}
            }
            
            print(f"Creating Razorpay order: {order_data}")  # ✅ Debug log
            order = self.client.order.create(data=order_data)
            return {'success': True, 'order': order}
        except Exception as e:
            print(f"Razorpay order error: {str(e)}")  # ✅ Debug log
            return {'success': False, 'error': str(e)}

    
    def verify_payment_signature(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str
    ) -> bool:
        """
        Verify Razorpay payment signature
        
        Args:
            razorpay_order_id: Order ID
            razorpay_payment_id: Payment ID
            razorpay_signature: Signature to verify
            
        Returns:
            True if signature is valid
        """
        try:
            params = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            
            self.client.utility.verify_payment_signature(params)
            return True
        except razorpay.errors.SignatureVerificationError:
            return False
    
    def capture_payment(
        self,
        payment_id: str,
        amount: Decimal,
        currency: str = 'USD'
    ) -> Dict[str, Any]:
        """
        Capture authorized payment
        
        Args:
            payment_id: Razorpay payment ID
            amount: Amount to capture
            currency: Currency code
            
        Returns:
            Capture result
        """
        try:
            amount_in_cents = int(amount * 100)
            
            capture = self.client.payment.capture(
                payment_id,
                amount_in_cents,
                {'currency': currency}
            )
            
            return {
                'success': True,
                'payment': capture
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_subscription(
        self,
        plan_id: str,
        customer_id: str,
        total_count: int = 12,
        quantity: int = 1,
        start_at: int = None,
        notes: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create Razorpay subscription
        
        Args:
            plan_id: Razorpay plan ID
            customer_id: Razorpay customer ID
            total_count: Total billing cycles
            quantity: Subscription quantity
            start_at: Start timestamp
            notes: Additional notes
            
        Returns:
            Subscription details
        """
        try:
            subscription_data = {
                'plan_id': plan_id,
                'customer_id': customer_id,
                'total_count': total_count,
                'quantity': quantity,
                'notes': notes or {}
            }
            
            if start_at:
                subscription_data['start_at'] = start_at
            
            subscription = self.client.subscription.create(data=subscription_data)
            
            return {
                'success': True,
                'subscription': subscription
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def cancel_subscription(
        self,
        subscription_id: str,
        cancel_at_cycle_end: bool = False
    ) -> Dict[str, Any]:
        """
        Cancel Razorpay subscription
        
        Args:
            subscription_id: Razorpay subscription ID
            cancel_at_cycle_end: Cancel at end of billing cycle
            
        Returns:
            Cancellation result
        """
        try:
            if cancel_at_cycle_end:
                subscription = self.client.subscription.cancel(
                    subscription_id,
                    {'cancel_at_cycle_end': 1}
                )
            else:
                subscription = self.client.subscription.cancel(subscription_id)
            
            return {
                'success': True,
                'subscription': subscription
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    def fetch_token(self, token_id):
        """
        Fetch payment token details from Razorpay
        
        Args:
            token_id: Razorpay token ID
            
        Returns:
            dict: Token details with success status
        """
        try:
            # Fetch token from Razorpay
            token = self.client.token.fetch(token_id)
            
            # Extract card details if it's a card
            card_data = {}
            if token.get('method') == 'card' and 'card' in token:
                card = token['card']
                card_data = {
                    'last4': card.get('last4', ''),
                    'network': card.get('network', ''),  # Visa, Mastercard, etc.
                    'issuer': card.get('issuer', ''),    # Bank name
                    'type': card.get('type', ''),        # credit/debit
                    'name': card.get('name', '')         # Cardholder name
                }
            
            return {
                'success': True,
                'method': token.get('method', 'card'),
                **card_data
            }
            
        except Exception as e:
            logger.error(f"Error fetching token {token_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    

    def fetch_customer_by_email(self, email: str) -> Dict[str, Any]:
        """
        ✅ NEW METHOD: Fetch Razorpay customer by email
        
        Args:
            email: Customer email address
            
        Returns:
            Customer details or empty list
        """
        try:
            # Razorpay API doesn't have direct email search,
            # but we can fetch all customers and filter
            # OR use the customer.all() with email filter if available
            
            # Try to fetch customers with email filter
            customers = self.client.customer.all({'email': email})
            
            if customers and 'items' in customers:
                return {
                    'success': True,
                    'customers': customers['items']
                }
            else:
                return {
                    'success': True,
                    'customers': []
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'customers': []
            }
    
    def fetch_customer(self, customer_id: str) -> Dict[str, Any]:
        """
        Fetch Razorpay customer by ID
        
        Args:
            customer_id: Razorpay customer ID
            
        Returns:
            Customer details
        """
        try:
            customer = self.client.customer.fetch(customer_id)
            
            return {
                'success': True,
                'customer': customer
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
        

    def fetch_payment_details(self, payment_id: str) -> Dict[str, Any]:
        """
        Fetch complete payment details from Razorpay
        
        Args:
            payment_id: Razorpay payment ID
            
        Returns:
            Dict with payment details including method-specific information
        """
        try:
            # Fetch payment from Razorpay
            payment = self.client.payment.fetch(payment_id)
            
            method_type = payment.get('method', '')
            result = {
                'success': True,
                'method_type': method_type,
                'email': payment.get('email', ''),
                'contact': payment.get('contact', ''),
                'amount': payment.get('amount', 0) / 100,  # Convert from paise
                'currency': payment.get('currency', 'USD'),
                'status': payment.get('status', ''),
            }
            
            # Extract method-specific details
            if method_type == 'card':
                card_info = payment.get('card', {})
                result.update({
                    'last4': card_info.get('last4', ''),
                    'card_network': card_info.get('network', ''),
                    'card_issuer': card_info.get('issuer', ''),
                    'card_type': card_info.get('type', ''),  # credit/debit
                    'card_name': card_info.get('name', ''),
                })
            
            elif method_type == 'upi':
                result.update({
                    'upi_vpa': payment.get('vpa', ''),
                })
            
            elif method_type == 'netbanking':
                result.update({
                    'bank_name': payment.get('bank', ''),
                })
            
            elif method_type == 'wallet':
                result.update({
                    'wallet_name': payment.get('wallet', ''),
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching payment {payment_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_refund(
        self,
        payment_id: str,
        amount: Decimal = None,
        notes: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create refund for payment
        
        Args:
            payment_id: Razorpay payment ID
            amount: Amount to refund (None for full refund)
            notes: Additional notes
            
        Returns:
            Refund details
        """
        try:
            refund_data = {
                'notes': notes or {}
            }
            
            if amount:
                refund_data['amount'] = int(amount * 100)
            
            refund = self.client.payment.refund(payment_id, refund_data)
            
            return {
                'success': True,
                'refund': refund
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_webhook_signature(
        self,
        webhook_body: str,
        webhook_signature: str
    ) -> bool:
        """
        Verify Razorpay webhook signature
        
        Args:
            webhook_body: Raw webhook body
            webhook_signature: Signature from header
            
        Returns:
            True if signature is valid
        """
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                webhook_body.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(
                expected_signature,
                webhook_signature
            )
        except Exception:
            return False
    
    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Fetch subscription details
        
        Args:
            subscription_id: Razorpay subscription ID
            
        Returns:
            Subscription details
        """
        try:
            subscription = self.client.subscription.fetch(subscription_id)
            return {
                'success': True,
                'subscription': subscription
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_plan(
        self,
        period: str,
        interval: int,
        amount: Decimal,
        currency: str = 'USD',
        notes: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create subscription plan
        
        Args:
            period: Billing period (daily, weekly, monthly, yearly)
            interval: Billing interval
            amount: Plan amount
            currency: Currency code
            notes: Additional notes
            
        Returns:
            Plan details
        """
        try:
            plan_data = {
                'period': period,
                'interval': interval,
                'item': {
                    'name': f"{period.capitalize()} Plan",
                    'amount': int(amount * 100),
                    'currency': currency
                },
                'notes': notes or {}
            }
            
            plan = self.client.plan.create(data=plan_data)
            
            return {
                'success': True,
                'plan': plan
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
        
    def create_customer(self, name: str, email: str) -> dict:
        """
        Create a Razorpay customer record.
        Args:
            name: Customer name
            email: Customer email
        Returns:
            Dict with success flag and customer info (or error)
        """
        try:
            customer_data = {
                "name": name,
                "email": email
            }
            customer = self.client.customer.create(data=customer_data)
            return {"success": True, "customer_id": customer.get("id"), "customer": customer}
        except Exception as e:
            return {"success": False, "error": str(e)}
