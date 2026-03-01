from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import os
from email.mime.image import MIMEImage


def send_email_with_logo(subject, template_name, context, recipient_list, fail_silently=False):
    """
    Helper function to send email with embedded logo
    """
    html_message = render_to_string(template_name, context)
    # Replace valid file path (used for local preview) with Content-ID (used for email embedding)
    html_message = html_message.replace('src="logo.png"', 'src="cid:logo"')
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL

    msg = EmailMultiAlternatives(subject, plain_message, from_email, recipient_list)
    msg.attach_alternative(html_message, "text/html")

    # Path to the logo file relative to this file (apps/users/utils.py)
    # Logo is in apps/users/templates/emails/logo.png
    current_dir = os.path.dirname(__file__)
    logo_path = os.path.join(current_dir, 'templates', 'emails', 'logo.png')
    
    if os.path.exists(logo_path):
        with open(logo_path, 'rb') as f:
            logo_data = f.read()
            logo = MIMEImage(logo_data)
            logo.add_header('Content-ID', '<logo>')
            logo.add_header('Content-Disposition', 'inline', filename='logo.png')
            msg.attach(logo)
    else:
        print(f"⚠️ WARNING: Email logo not found at {logo_path}")
        # If strict requirement, you might want to raise an error here
        # raise FileNotFoundError(f"Logo not found at {logo_path}")
    
    try:
        msg.send(fail_silently=fail_silently)
        return True
    except Exception as e:
        if not fail_silently:
            raise e
        return False


def send_verification_email(user, token):
    """
    Send email verification email to user
    """
    subject = "Verify your email - Glad Monet"

    # Build verification URL - points to backend which will verify and redirect
    backend_url = getattr(settings, "BACKEND_URL", "http://127.0.0.1:8000")
    verification_url = f"{backend_url}/api/auth/verify-email/?token={token}"
    context = {
        "user": user,
        "verification_url": verification_url,
    }

    send_email_with_logo(
        subject=subject,
        template_name="emails/verification_email.html",
        context=context,
        recipient_list=[user.email]
    )


def send_forgot_password_otp(user, otp_code):
    """
    Send OTP for forgot password request
    """
    subject = "Password Reset Verification - Glad Monet"
    context = {
        "user": user,
        "otp_code": otp_code,
    }

    send_email_with_logo(
        subject=subject,
        template_name="emails/forgot_password_otp_email.html",
        context=context,
        recipient_list=[user.email]
    )


def send_password_reset_email(user, token):
    """
    Send password reset email to user
    """
    subject = "Reset your password - Glad Monet"
    # Build reset URL
    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:8080")
    reset_url = f"{frontend_url}/reset-password?token={token}"

    context = {
        "user": user,
        "reset_url": reset_url,
    }

    send_email_with_logo(
        subject=subject,
        template_name="emails/password_reset_email.html",
        context=context,
        recipient_list=[user.email]
    )


def send_welcome_email(user):
    """
    Send welcome email to new verified user
    """
    subject = "Welcome to Glad Monet!"

    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:8080")
    context = {
        "user": user,
        "frontend_url": frontend_url,
    }

    send_email_with_logo(
        subject=subject,
        template_name="emails/welcome_email.html",
        context=context,
        recipient_list=[user.email],
        fail_silently=True
    )


def send_password_change_otp(user, otp_code):
    """
    Send OTP for password change request
    """
    subject = "Password Change Verification - Glad Monet"
    context = {
        "user": user,
        "otp_code": otp_code,
    }

    send_email_with_logo(
        subject=subject,
        template_name="emails/password_change_otp_email.html",
        context=context,
        recipient_list=[user.email]
    )


def send_enterprise_contact_email(contact):
    """
    Send email notification to sales team about new enterprise contact

    Args:
        contact: EnterpriseContact instance
    """
    # Email to your sales team
    recipient_email = getattr(settings, "SALES_EMAIL", settings.DEFAULT_FROM_EMAIL)
    backend_url = getattr(settings, "BACKEND_URL", "http://127.0.0.1:8000")

    subject = f"🚀 New Enterprise Inquiry from {contact.company_name}"
    context = {
        "contact": contact,
        "backend_url": backend_url,
    }

    try:
        send_email_with_logo(
            subject=subject,
            template_name="users/emails/enterprise_contact_email.html",
            context=context,
            recipient_list=[recipient_email]
        )
        print(f"✅ Enterprise contact email sent to {recipient_email}")
    except Exception as e:
        print(f"❌ Failed to send enterprise contact email: {e}")
        raise
