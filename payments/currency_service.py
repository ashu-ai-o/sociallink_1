"""
Currency Conversion Service
Fetches live exchange rates and converts USD to local currencies
"""

import requests
import logging
from decimal import Decimal
from typing import Dict, Optional, Tuple
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class CurrencyService:
    """
    Service for currency conversion with live exchange rates
    Uses exchangerate-api.com (free tier: 1500 requests/month)
    """
    
    # Currency mapping by country code
    COUNTRY_CURRENCY_MAP = {
        'US': 'USD',
        'IN': 'INR',
        'AE': 'AED',
        'GB': 'GBP',
        'CA': 'CAD',
        'AU': 'AUD',
        'SG': 'SGD',
        'MY': 'MYR',
        'SA': 'SAR',
        'QA': 'QAR',
        'KW': 'KWD',
        'BH': 'BHD',
        'OM': 'OMR',
        'EU': 'EUR',
        'DE': 'EUR',
        'FR': 'EUR',
        'IT': 'EUR',
        'ES': 'EUR',
        'NL': 'EUR',
        'JP': 'JPY',
        'CN': 'CNY',
        'KR': 'KRW',
        'BR': 'BRL',
        'MX': 'MXN',
        'ZA': 'ZAR',
        # Add more as needed
    }
    
    # Currency symbols
    CURRENCY_SYMBOLS = {
        'USD': '$',
        'INR': '₹',
        'AED': 'د.إ',
        'GBP': '£',
        'EUR': '€',
        'CAD': 'C$',
        'AUD': 'A$',
        'SGD': 'S$',
        'MYR': 'RM',
        'SAR': 'ر.س',
        'QAR': 'ر.ق',
        'KWD': 'د.ك',
        'BHD': 'د.ب',
        'OMR': 'ر.ع',
        'JPY': '¥',
        'CNY': '¥',
        'KRW': '₩',
        'BRL': 'R$',
        'MXN': 'Mex$',
        'ZAR': 'R',
    }
    
    # Razorpay supported currencies
    RAZORPAY_SUPPORTED = [
        'INR', 'USD', 'AED', 'GBP', 'EUR', 'SGD', 'MYR', 'AUD'
    ]
    
    def __init__(self):
        # Use free exchangerate-api.com or similar
        # Alternative: https://api.exchangerate-api.com/v4/latest/USD
        self.api_url = "https://api.exchangerate-api.com/v4/latest/USD"
        self.cache_timeout = 3600  # 1 hour cache
        
    def get_currency_for_country(self, country_code: str) -> str:
        """
        Get currency code for a country
        
        Args:
            country_code: ISO 3166-1 alpha-2 country code (e.g., 'IN', 'AE')
            
        Returns:
            Currency code (e.g., 'INR', 'AED') or 'USD' as fallback
        """
        return self.COUNTRY_CURRENCY_MAP.get(country_code.upper(), 'USD')
    
    def get_currency_symbol(self, currency_code: str) -> str:
        """Get currency symbol"""
        return self.CURRENCY_SYMBOLS.get(currency_code, currency_code)
    
    def is_razorpay_supported(self, currency_code: str) -> bool:
        """Check if currency is supported by Razorpay"""
        return currency_code in self.RAZORPAY_SUPPORTED
    
    def get_live_exchange_rates(self) -> Optional[Dict[str, float]]:
        """
        Fetch live exchange rates from API with caching
        
        Returns:
            Dictionary of currency rates or None on failure
        """
        # Check cache first
        cache_key = 'exchange_rates_usd'
        cached_rates = cache.get(cache_key)
        
        if cached_rates:
            logger.info("Using cached exchange rates")
            return cached_rates
        
        try:
            logger.info("Fetching live exchange rates...")
            response = requests.get(self.api_url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                rates = data.get('rates', {})
                
                # Cache for 1 hour
                cache.set(cache_key, rates, self.cache_timeout)
                logger.info(f"Fetched {len(rates)} exchange rates")
                
                return rates
            else:
                logger.error(f"Exchange rate API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to fetch exchange rates: {e}")
            return None
    
    def convert_usd_to_currency(
        self,
        usd_amount: Decimal,
        target_currency: str
    ) -> Tuple[Decimal, float, bool]:
        """
        Convert USD amount to target currency
        
        Args:
            usd_amount: Amount in USD
            target_currency: Target currency code
            
        Returns:
            Tuple of (converted_amount, exchange_rate, success)
        """
        # If target is USD, return as-is
        if target_currency == 'USD':
            return usd_amount, 1.0, True
        
        # Get live rates
        rates = self.get_live_exchange_rates()
        
        if not rates:
            logger.warning("Using fallback exchange rates")
            # Fallback rates (approximate)
            rates = {
                'INR': 83.0,
                'AED': 3.67,
                'GBP': 0.79,
                'EUR': 0.92,
                'CAD': 1.36,
                'AUD': 1.52,
                'SGD': 1.34,
                'MYR': 4.47,
                'SAR': 3.75,
            }
        
        exchange_rate = rates.get(target_currency)
        
        if not exchange_rate:
            logger.error(f"No exchange rate for {target_currency}")
            return usd_amount, 1.0, False
        
        converted = Decimal(str(usd_amount)) * Decimal(str(exchange_rate))
        
        # Round to 2 decimal places
        converted = converted.quantize(Decimal('0.01'))
        
        logger.info(
            f"Converted ${usd_amount} to {converted} {target_currency} "
            f"(rate: {exchange_rate})"
        )
        
        return converted, exchange_rate, True
    
    def get_payment_details(
        self,
        usd_amount: Decimal,
        country_code: str
    ) -> Dict:
        """
        Get complete payment details with currency conversion
        
        Args:
            usd_amount: Base amount in USD
            country_code: User's country code
            
        Returns:
            Dictionary with all payment details
        """
        # Determine currency
        local_currency = self.get_currency_for_country(country_code)
        
        # Check if Razorpay supports it
        if not self.is_razorpay_supported(local_currency):
            logger.warning(
                f"{local_currency} not supported by Razorpay, using USD"
            )
            local_currency = 'USD'
        
        # Convert amount
        converted_amount, rate, success = self.convert_usd_to_currency(
            usd_amount,
            local_currency
        )
        
        return {
            'base_amount_usd': float(usd_amount),
            'local_currency': local_currency,
            'local_amount': float(converted_amount),
            'exchange_rate': rate,
            'currency_symbol': self.get_currency_symbol(local_currency),
            'conversion_success': success,
            'country_code': country_code
        }