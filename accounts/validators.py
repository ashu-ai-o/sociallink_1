from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import re


class ComplexPasswordValidator:
    """
    Validate password complexity:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    """
    
    def validate(self, password, user=None):
        if len(password) < 8:
            raise ValidationError(
                _("Password must be at least 8 characters long."),
                code='password_too_short',
            )
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("Password must contain at least one uppercase letter."),
                code='password_no_upper',
            )
        
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                _("Password must contain at least one lowercase letter."),
                code='password_no_lower',
            )
        
        if not re.search(r'\d', password):
            raise ValidationError(
                _("Password must contain at least one number."),
                code='password_no_number',
            )
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                _("Password must contain at least one special character (!@#$%^&*)."),
                code='password_no_special',
            )
    
    def get_help_text(self):
        return _(
            "Your password must contain at least 8 characters, including uppercase, "
            "lowercase, numbers, and special characters."
        )


class CommonPasswordValidator:
    """Prevent common passwords"""
    
    COMMON_PASSWORDS = [
        'password', 'password123', '12345678', 'qwerty', 'abc123',
        'letmein', 'welcome', 'monkey', '123456789', 'password1'
    ]
    
    def validate(self, password, user=None):
        if password.lower() in self.COMMON_PASSWORDS:
            raise ValidationError(
                _("This password is too common. Please choose a more unique password."),
                code='password_too_common',
            )
    
    def get_help_text(self):
        return _("Your password can't be a commonly used password.")


