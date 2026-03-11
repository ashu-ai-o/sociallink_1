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
    # Use remote logo if possible for better compatibility
    logo_url = "https://i.ibb.co/vz0L5Gj/dmme-logo.png" # Example remote logo
    html_message = html_message.replace('src="logo.png"', f'src="{logo_url}"')
    html_message = html_message.replace('src="logo_black_trans.svg"', f'src="{logo_url}"')
    
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL

    msg = EmailMultiAlternatives(subject, plain_message, from_email, recipient_list)
    msg.attach_alternative(html_message, "text/html")

    
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
            template_name="emails/enterprise_contact_email.html",
            context=context,
            recipient_list=[recipient_email]
        )
        print(f"✅ Enterprise contact email sent to {recipient_email}")
    except Exception as e:
        print(f"❌ Failed to send enterprise contact email: {e}")
        raise
