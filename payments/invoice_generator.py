import os
from io import BytesIO
from decimal import Decimal
from django.conf import settings
from django.template.loader import render_to_string

import logging

logger = logging.getLogger(__name__)

# --- PDF Generator Discovery ---
# We check which generators are actually usable in this environment
HAS_WEASYPRINT = False
try:
    from weasyprint import HTML
    # WeasyPrint requires GTK+ libraries which might be missing on Windows/Server
    # Calling a small test to ensure the DLLs are actually loadable
    HAS_WEASYPRINT = True
except Exception:
    HAS_WEASYPRINT = False

HAS_XHTML2PDF = False
try:
    from xhtml2pdf import pisa
    HAS_XHTML2PDF = True
except ImportError:
    HAS_XHTML2PDF = False

def generate_invoice_pdf(payment):
    """
    Generate a professional PDF invoice for a given Payment.
    Takes a Payment object that belongs to a UserSubscription.
    """

    user = payment.user
    user_name = user.get_full_name() or user.username
    metadata = payment.metadata or {}
    
    billing_cycle = metadata.get('billing_cycle', 'monthly')
    plan_name = "Subscription Plan"
    if payment.subscription and payment.subscription.plan:
        plan_name = payment.subscription.plan.display_name
        
    created_at = payment.created_at or timezone.now()
    completed_at = payment.completed_at or created_at
    date_formatted = completed_at.strftime('%b %d, %Y')
    
    def safe_decimal(val, default='0'):
        if val is None: return Decimal(default)
        try:
            return Decimal(str(val))
        except (ValueError, TypeError, Exception):
            return Decimal(default)

    local_currency = metadata.get('local_currency', payment.currency or 'USD')
    local_amount = safe_decimal(metadata.get('local_amount', payment.amount), '0')
    
    proration_credit_usd = safe_decimal(metadata.get('proration_credit_usd', '0'), '0')
    exchange_rate = safe_decimal(metadata.get('exchange_rate', '1'), '1')
    proration_credit_local = proration_credit_usd * exchange_rate
    
    base_local_amount = safe_decimal(metadata.get('base_local_amount', local_amount), '0')
    tax_name = metadata.get('tax_name', '')
    tax_amount_local = safe_decimal(metadata.get('tax_amount_local', '0'), '0')
    
    subtotal = base_local_amount - proration_credit_local
    final_total = subtotal + tax_amount_local

    context = {
        'invoice_number': payment.invoice_number or str(payment.id)[:8],
        'user_name': user_name,
        'user_email': user.email,
        'user_country': metadata.get('country_code', 'IN' if local_currency == 'INR' else 'US'),
        'date_formatted': date_formatted,
        'razorpay_payment_id': payment.razorpay_payment_id or "—",
        'plan_name': plan_name,
        'billing_cycle': billing_cycle,
        'local_currency': local_currency,
        'base_local_amount': base_local_amount,
        'proration_credit_local': proration_credit_local,
        'subtotal': subtotal,
        'tax_name': tax_name,
        'tax_amount_local': tax_amount_local,
        'final_total': final_total
    }

    # Render HTML from template
    html_string = render_to_string('emails/invoice_pdf.html', context)
    
    # Try WeasyPrint (Premium Engine)
    if HAS_WEASYPRINT:
        try:
            return HTML(string=html_string).write_pdf()
        except Exception as e:
            logger.error(f"WeasyPrint execution error: {e}")

    # Fallback to xhtml2pdf (Portable Engine)
    if HAS_XHTML2PDF:
        try:
            result = BytesIO()
            pisa_status = pisa.CreatePDF(html_string, dest=result, encoding='utf-8')
            if not pisa_status.err:
                return result.getvalue()
            else:
                 logger.error(f"xhtml2pdf error: {pisa_status.err}")
        except Exception as e:
            logger.error(f"xhtml2pdf execution error: {e}")
    
    # Ultimate fallback if everything fails
    return b"Error: PDF generation failed because system dependencies for WeasyPrint/xhtml2pdf are missing."
