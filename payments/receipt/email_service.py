"""
Email Service for Payment Notifications
Handles sending payment receipts, failure notifications, and PDF generation
"""
import logging
import os
from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import datetime
from io import BytesIO
from django.conf import settings as django_settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

# PDF Generation
from payments.invoice_generator import generate_invoice_pdf

from payments.models import Payment, UserSubscription, EmailLog

logger = logging.getLogger(__name__)


class EmailService:
    """
    Centralized email service for payment notifications
    """
    
    @staticmethod
    def send_payment_receipt(payment_id: str) -> Dict[str, Any]:
        """
        Send payment receipt email with PDF attachment
        
        Args:
            payment_id: UUID of the payment
            
        Returns:
            Dict with success status and message
        """
        try:
            # Get payment details
            payment = Payment.objects.select_related(
                'user', 'subscription', 'subscription__plan'
            ).get(id=payment_id)

            # Ensure invoice number exists before building the email
            if not payment.invoice_number:
                payment.generate_invoice_number()
                payment.save(update_fields=['invoice_number'])
            
            # Check user email preferences
            if not EmailService._can_send_email(payment.user, 'payment_receipt'):
                logger.info(f"User {payment.user.email} has opted out of payment receipt emails")
                return {
                    'success': True,
                    'message': 'User opted out',
                    'skipped': True
                }
            
            # Prepare email context
            context = EmailService._prepare_receipt_context(payment)
            
            # Generate PDF receipt using WeasyPrint
            pdf_bytes = generate_invoice_pdf(payment)
            
            # Render HTML email
            html_message = render_to_string(
                'emails/payment_receipt.html',
                context
            )
            text_message = strip_tags(html_message)
            
            # Create email
            subject = f"Payment Receipt - Invoice #{payment.invoice_number}"
            from_email = django_settings.DEFAULT_FROM_EMAIL
            recipient_list = [payment.user.email]
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=from_email,
                to=recipient_list
            )
            email.attach_alternative(html_message, "text/html")
            
            # Attach PDF
            if pdf_bytes:
                email.attach(
                    f"Invoice_{payment.invoice_number}.pdf",
                    pdf_bytes,
                    'application/pdf'
                )
            
            # Send email
            email.send(fail_silently=False)
            
            # Log email
            EmailLog.objects.create(
                user=payment.user,
                payment=payment,
                email_type='payment_receipt',
                recipient=payment.user.email,
                subject=subject,
                status='sent',
                metadata={
                    'payment_id': str(payment.id),
                    'invoice_number': payment.invoice_number,
                    'amount': str(payment.amount)
                }
            )
            
            logger.info(f"Payment receipt sent to {payment.user.email} for payment {payment.id}")
            
            return {
                'success': True,
                'message': 'Receipt email sent successfully',
                'email': payment.user.email
            }
            
        except Payment.DoesNotExist:
            logger.error(f"Payment {payment_id} not found")
            return {
                'success': False,
                'error': 'Payment not found'
            }
        except Exception as e:
            logger.error(f"Error sending receipt email: {str(e)}", exc_info=True)
            
            # Log failed email
            try:
                EmailLog.objects.create(
                    payment_id=payment_id,
                    email_type='payment_receipt',
                    status='failed',
                    error_message=str(e)
                )
            except Exception:
                pass
            
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def send_payment_failure(payment_id: str) -> Dict[str, Any]:
        """
        Send payment failure notification email
        
        Args:
            payment_id: UUID of the failed payment
            
        Returns:
            Dict with success status and message
        """
        try:
            # Get payment details
            payment = Payment.objects.select_related(
                'user', 'subscription', 'subscription__plan'
            ).get(id=payment_id)
            
            # Check user email preferences
            if not EmailService._can_send_email(payment.user, 'payment_failure'):
                logger.info(f"User {payment.user.email} has opted out of payment failure emails")
                return {
                    'success': True,
                    'message': 'User opted out',
                    'skipped': True
                }
            
            # Prepare email context
            context = EmailService._prepare_failure_context(payment)
            
            # Render HTML email
            html_message = render_to_string(
                'emails/payment_failure.html',
                context
            )
            text_message = strip_tags(html_message)
            
            # Create email
            subject = f"Payment Failed - Action Required"
            from_email = django_settings.DEFAULT_FROM_EMAIL
            recipient_list = [payment.user.email]
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=from_email,
                to=recipient_list
            )
            email.attach_alternative(html_message, "text/html")
            
            # Send email
            email.send(fail_silently=False)
            
            # Log email
            EmailLog.objects.create(
                user=payment.user,
                payment=payment,
                email_type='payment_failure',
                recipient=payment.user.email,
                subject=subject,
                status='sent',
                metadata={
                    'payment_id': str(payment.id),
                    'failure_reason': payment.failure_reason,
                    'amount': str(payment.amount)
                }
            )
            
            logger.info(f"Payment failure email sent to {payment.user.email} for payment {payment.id}")
            
            return {
                'success': True,
                'message': 'Failure notification sent successfully',
                'email': payment.user.email
            }
            
        except Payment.DoesNotExist:
            logger.error(f"Payment {payment_id} not found")
            return {
                'success': False,
                'error': 'Payment not found'
            }
        except Exception as e:
            logger.error(f"Error sending failure email: {str(e)}", exc_info=True)
            
            # Log failed email
            try:
                EmailLog.objects.create(
                    payment_id=payment_id,
                    email_type='payment_failure',
                    status='failed',
                    error_message=str(e)
                )
            except Exception:
                pass
            
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def _can_send_email(user, email_type: str) -> bool:
        """Check if user allows this type of email via email_preferences JSONField on User"""
        try:
            # email_preferences is a JSONField on accounts.User
            email_prefs = getattr(user, 'email_preferences', None) or {}
            return email_prefs.get(email_type, True)
        except Exception as e:
            logger.warning(f"Could not check email preference for user {user.id}: {e}")
            return True  # Default to sending
    
    @staticmethod
    def _prepare_receipt_context(payment: Payment) -> Dict[str, Any]:
        """Prepare context data for receipt email"""
        subscription = payment.subscription
        plan = subscription.plan if subscription else None
        # Extract tax and local currency details
        metadata = payment.metadata or {}
        local_currency = metadata.get('local_currency', payment.currency)
        base_local_amount = Decimal(str(metadata.get('base_local_amount', payment.amount)))
        tax_amount_local = Decimal(str(metadata.get('tax_amount_local', '0')))
        
        proration_credit_usd = Decimal(str(metadata.get('proration_credit_usd', '0')))
        exchange_rate = Decimal(str(metadata.get('exchange_rate', '1')))
        proration_credit_local = proration_credit_usd * exchange_rate
        
        subtotal = base_local_amount - proration_credit_local
        final_total = subtotal + tax_amount_local
        
        context = {
            'user': payment.user,
            'payment': payment,
            'subscription': subscription,
            'plan': plan,
            'invoice_number': payment.invoice_number,
            'payment_date': payment.completed_at or payment.created_at,
            'amount': f"{final_total:,.2f}",
            'currency': local_currency,
            'payment_method': EmailService._get_payment_method_display(payment),
            'company_name': 'dm-me',
            'company_email': 'support@dm-me.com',
            'company_address': 'Agra, Uttar Pradesh, India',
            'frontend_url': getattr(django_settings, 'FRONTEND_URL', 'https://dm-me.com'),
            'current_year': datetime.now().year,
        }
        
        # Add plan-specific details
        if payment.payment_type == 'subscription':
            context['payment_type_display'] = 'Subscription Payment'
            context['plan_name'] = plan.display_name if plan else 'N/A'
            context['billing_cycle'] = subscription.billing_cycle if subscription else 'N/A'
            context['tokens_included'] = plan.monthly_token_credits if plan else 0
            context['period_start'] = subscription.current_period_start if subscription else None
            context['period_end'] = subscription.current_period_end if subscription else None
        elif payment.payment_type == 'token_purchase':
            context['payment_type_display'] = 'Token Package Purchase'
            context['tokens_purchased'] = payment.tokens_purchased
        
        return context
    
    @staticmethod
    def _prepare_failure_context(payment: Payment) -> Dict[str, Any]:
        """Prepare context data for failure email"""
        subscription = payment.subscription
        plan = subscription.plan if subscription else None
        
        context = {
            'user': payment.user,
            'payment': payment,
            'subscription': subscription,
            'plan': plan,
            'failure_reason': EmailService._get_friendly_error_message(payment.failure_reason),
            'amount': payment.amount,
            'currency': payment.currency,
            'payment_date': payment.created_at,
            'retry_url': f"{django_settings.FRONTEND_URL}/pricing",
            'support_email': 'support@dm-me.com',
            'company_name': 'dm-me',
            'frontend_url': django_settings.FRONTEND_URL,
            'current_year': datetime.now().year,
        }
        
        return context
    
    @staticmethod
    def _get_payment_method_display(payment: Payment) -> str:
        """Get user-friendly payment method name"""
        metadata = payment.metadata or {}
        method = metadata.get('payment_method', 'Card')
        
        method_map = {
            'card': 'Credit/Debit Card',
            'upi': 'UPI',
            'netbanking': 'Net Banking',
            'wallet': 'Wallet'
        }
        
        return method_map.get(method.lower(), method)
    
    @staticmethod
    def _get_friendly_error_message(error_reason: str) -> str:
        """Convert technical error to user-friendly message"""
        if not error_reason:
            return "Payment could not be processed. Please try again."
        
        error_lower = error_reason.lower()
        
        if 'insufficient' in error_lower or 'balance' in error_lower:
            return "Insufficient funds in your account. Please check your balance and try again."
        elif 'declined' in error_lower or 'rejected' in error_lower:
            return "Your payment was declined by the bank. Please try a different payment method."
        elif 'expired' in error_lower:
            return "Your card has expired. Please use a different card."
        elif 'invalid' in error_lower:
            return "Invalid payment details. Please check your information and try again."
        elif 'limit' in error_lower:
            return "Transaction limit exceeded. Please contact your bank or try a smaller amount."
        elif 'timeout' in error_lower or 'timed out' in error_lower:
            return "Payment request timed out. Please try again."
        else:
            return error_reason