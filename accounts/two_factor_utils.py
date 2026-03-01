"""
Two-Factor Authentication (2FA) Utilities
Using TOTP (Time-Based One-Time Password) with pyotp
"""
import pyotp
import qrcode
import io
import base64
import secrets
import hashlib
from django.conf import settings


class TwoFactorAuth:
    """Handle all 2FA operations"""
    
    @staticmethod
    def generate_secret():
        """
        Generate a random secret key for TOTP
        Returns: 32-character base32 secret
        """
        return pyotp.random_base32()
    
    @staticmethod
    def generate_qr_code(user, secret):
        """
        Generate QR code for Google Authenticator
        
        Args:
            user: User object
            secret: TOTP secret key
            
        Returns:
            Base64 encoded PNG image of QR code
        """
        # Create provisioning URI
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name=getattr(settings, 'SITE_NAME', 'AI Platform')
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    @staticmethod
    def verify_token(secret, token):
        """
        Verify TOTP token
        
        Args:
            secret: User's TOTP secret
            token: 6-digit code from authenticator app
            
        Returns:
            Boolean: True if valid, False otherwise
        """
        if not secret or not token:
            return False
        
        totp = pyotp.TOTP(secret)
        
        # Verify with 30-second window (allows for slight time drift)
        return totp.verify(token, valid_window=1)
    
    @staticmethod
    def generate_backup_codes(count=10):
        """
        Generate backup codes for account recovery
        
        Args:
            count: Number of backup codes to generate (default 10)
            
        Returns:
            List of hashed backup codes for storage,
            List of plain codes to show user (only shown once)
        """
        plain_codes = []
        hashed_codes = []
        
        for _ in range(count):
            # Generate 8-character code
            code = secrets.token_hex(4).upper()
            plain_codes.append(code)
            
            # Hash for storage
            hashed = hashlib.sha256(code.encode()).hexdigest()
            hashed_codes.append(hashed)
        
        return hashed_codes, plain_codes
    
    @staticmethod
    def verify_backup_code(stored_codes, input_code):
        """
        Verify a backup code and remove it if valid
        
        Args:
            stored_codes: List of hashed backup codes
            input_code: Plain backup code from user
            
        Returns:
            Tuple: (is_valid: bool, remaining_codes: list)
        """
        if not stored_codes or not input_code:
            return False, stored_codes
        
        # Hash input code
        input_hash = hashlib.sha256(input_code.upper().encode()).hexdigest()
        
        # Check if it exists
        if input_hash in stored_codes:
            # Remove used code
            remaining = [code for code in stored_codes if code != input_hash]
            return True, remaining
        
        return False, stored_codes
    
    @staticmethod
    def get_current_token(secret):
        """
        Get current TOTP token (for testing/debugging)
        
        Args:
            secret: TOTP secret
            
        Returns:
            Current 6-digit token
        """
        totp = pyotp.TOTP(secret)
        return totp.now()


# Helper functions for views
def setup_2fa_for_user(user):
    """
    Initialize 2FA setup for a user
    
    Returns:
        dict: {
            'secret': str,
            'qr_code': str (base64 image),
            'backup_codes': list (plain codes)
        }
    """
    # Generate secret
    secret = TwoFactorAuth.generate_secret()
    
    # Generate QR code
    qr_code = TwoFactorAuth.generate_qr_code(user, secret)
    
    # Generate backup codes
    hashed_codes, plain_codes = TwoFactorAuth.generate_backup_codes()
    
    # DON'T save to database yet - only after verification
    return {
        'secret': secret,
        'qr_code': qr_code,
        'backup_codes': plain_codes,
        'hashed_backup_codes': hashed_codes
    }


def enable_2fa_for_user(user, secret, hashed_backup_codes):
    """
    Enable 2FA after successful verification

    Args:
        user: User object
        secret: TOTP secret
        hashed_backup_codes: List of hashed backup codes
    """
    from django.utils import timezone

    user.two_factor_enabled = True
    user.two_factor_secret = secret
    user.backup_codes = hashed_backup_codes
    user.two_factor_enabled_at = timezone.now()
    user.save(update_fields=[
        'two_factor_enabled',
        'two_factor_secret',
        'backup_codes',
        'two_factor_enabled_at'
    ])


def disable_2fa_for_user(user):
    """
    Disable 2FA for a user
    """
    user.two_factor_enabled = False
    user.two_factor_secret = None
    user.backup_codes = []
    user.two_factor_enabled_at = None
    user.save(update_fields=[
        'two_factor_enabled',
        'two_factor_secret',
        'backup_codes',
        'two_factor_enabled_at'
    ])
