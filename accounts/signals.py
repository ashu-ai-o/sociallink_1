from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
from .utils import send_welcome_email


@receiver(post_save, sender=User)



def user_post_save(sender, instance, created, **kwargs):
    """
    Handle actions after user is saved
    Send welcome email ONLY ONCE after email verification
    """
    # Don't send on user creation
    if created:
        return
    
    # Only proceed if email was just verified and welcome email hasn't been sent
    if instance.is_email_verified and not instance.welcome_email_sent:
        try:
            send_welcome_email(instance)
            # Mark welcome email as sent to prevent duplicate sends
            User.objects.filter(pk=instance.pk).update(welcome_email_sent=True)
        except Exception as e:
            # Log error but don't fail
            print(f"Failed to send welcome email to {instance.email}: {e}")
