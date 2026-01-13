import re
from django.core.exceptions import ValidationError
from django.utils.html import escape
import bleach


class InputSanitizer:
    """Sanitize user inputs to prevent XSS and injection attacks"""
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 500) -> str:
        """
        Sanitize plain text input
        - Remove HTML tags
        - Escape special characters
        - Trim to max length
        """
        if not text:
            return ""
        
        # Remove HTML tags
        text = bleach.clean(text, tags=[], strip=True)
        
        # Escape special characters
        text = escape(text)
        
        # Trim to max length
        text = text[:max_length]
        
        return text.strip()
    
    @staticmethod
    def sanitize_instagram_username(username: str) -> str:
        """
        Sanitize Instagram username
        Only allow alphanumeric, dots, and underscores
        """
        if not username:
            raise ValidationError("Username cannot be empty")
        
        # Remove @ if present
        username = username.lstrip('@')
        
        # Only allow valid Instagram username characters
        if not re.match(r'^[a-zA-Z0-9._]+$', username):
            raise ValidationError("Invalid Instagram username format")
        
        if len(username) > 30:
            raise ValidationError("Username too long")
        
        return username.lower()
    
    @staticmethod
    def sanitize_url(url: str) -> str:
        """
        Sanitize URL input
        Only allow http/https protocols
        """
        if not url:
            return ""
        
        # Only allow http/https
        if not re.match(r'^https?://', url):
            raise ValidationError("URL must start with http:// or https://")
        
        # Basic URL validation
        if not re.match(
            r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$',
            url
        ):
            raise ValidationError("Invalid URL format")
        
        if len(url) > 500:
            raise ValidationError("URL too long")
        
        return url
    
    @staticmethod
    def sanitize_json_field(data: dict) -> dict:
        """
        Sanitize JSON field data
        """
        if not isinstance(data, dict):
            return {}
        
        sanitized = {}
        for key, value in data.items():
            # Sanitize keys
            clean_key = bleach.clean(str(key), tags=[], strip=True)[:50]
            
            # Sanitize values
            if isinstance(value, str):
                clean_value = bleach.clean(value, tags=[], strip=True)[:500]
            elif isinstance(value, (int, float, bool)):
                clean_value = value
            elif isinstance(value, dict):
                clean_value = InputSanitizer.sanitize_json_field(value)
            elif isinstance(value, list):
                clean_value = [
                    InputSanitizer.sanitize_text(str(item)) 
                    for item in value[:50]  # Limit array size
                ]
            else:
                clean_value = None
            
            sanitized[clean_key] = clean_value
        
        return sanitized
