# payments/utils.py

from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

def calculate_proration(current_subscription, new_plan, new_billing_cycle='monthly'):
    """
    Calculate proration amount for plan change in base USD.
    When a plan is changed, the user is billed for a FULL new billing cycle,
    and any unused time from their current cycle is applied as a discount.
    
    Returns:
        dict: {
            'credit_amount_usd': Decimal,  # Credit from current plan in USD
            'new_amount_usd': Decimal,      # Cost of new plan in USD
            'prorated_amount_usd': Decimal, # Final amount to charge in USD
            'days_remaining': int,
            'explanation': str
        }
    """
    now = timezone.now()
    
    period_start = current_subscription.current_period_start or now
    period_end = current_subscription.current_period_end or now
    
    period_total_days = max(1, (period_end - period_start).days)
    days_remaining = max(0, (period_end - now).days)
    
    # Calculate credit from current plan
    if current_subscription.billing_cycle == 'annual':
        old_period_amount = current_subscription.plan.annual_price
    else:
        old_period_amount = current_subscription.plan.monthly_price
    
    daily_rate_current = Decimal(str(old_period_amount)) / Decimal(period_total_days)
    credit_amount_usd = daily_rate_current * Decimal(days_remaining)
    
    # Calculate new plan cost
    if new_billing_cycle == 'annual':
        new_amount_usd = Decimal(str(new_plan.annual_price))
    else:
        new_amount_usd = Decimal(str(new_plan.monthly_price))
    
    prorated_amount_usd = max(Decimal('0'), new_amount_usd - credit_amount_usd)
    
    return {
        'credit_amount_usd': round(credit_amount_usd, 2),
        'new_amount_usd': round(new_amount_usd, 2),
        'prorated_amount_usd': round(prorated_amount_usd, 2),
        'days_remaining': days_remaining,
        'explanation': f"Unused credit of ${credit_amount_usd:.2f} applied to new ${new_amount_usd:.2f} plan."
    }

def calculate_tax(amount: Decimal, country_code: str) -> dict:
    """
    Calculate applicable tax based on user's country code.
    Reads dynamically from the Database via TaxRate model.
    
    Args:
        amount (Decimal): The pre-tax amount
        country_code (str): Two-letter ISO country code (e.g., 'IN', 'US', 'GB')
        
    Returns:
        dict: {
            'tax_rate': Decimal,      # e.g. 0.18 for 18%
            'tax_amount': Decimal,    # The computed tax
            'total_amount': Decimal,  # The final amount including tax
            'tax_name': str           # Name of the tax (e.g., 'GST', 'VAT')
        }
    """
    from payments.models import TaxRate
    
    country_code = str(country_code).upper()
    
    # Check for direct country match
    tax_record = TaxRate.objects.filter(country_code=country_code, is_active=True).first()
    
    # Fallback checking - if EU member
    if getattr(tax_record, 'rate', None) is None:
        EU_COUNTRIES = {'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'AT', 'SE', 'DK', 'FI', 'IE', 'PT'}
        if country_code in EU_COUNTRIES:
            tax_record = TaxRate.objects.filter(country_code='EU', is_active=True).first()
            
    # Ultimate Fallback
    if getattr(tax_record, 'rate', None) is None:
        tax_record = TaxRate.objects.filter(country_code='DEFAULT', is_active=True).first()

    # Ensure amount is a Decimal
    amount = Decimal(str(amount))
    
    # If absolutely nothing is configured in DB, default to 0
    tax_rate = tax_record.rate if tax_record else Decimal('0.00')
    tax_name = tax_record.tax_name if tax_record else 'Tax (0%)'

    tax_amount = (amount * tax_rate).quantize(Decimal('0.01'))
    total_amount = amount + tax_amount

    return {
        'tax_rate': tax_rate,
        'tax_amount': tax_amount,
        'total_amount': total_amount,
        'tax_name': tax_name
    }
