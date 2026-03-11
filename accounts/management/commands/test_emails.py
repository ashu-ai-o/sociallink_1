from django.core.management.base import BaseCommand
from accounts.models import User
from accounts.utils import send_welcome_email
from payments.models import Payment
from payments.receipt.email_service import EmailService
import uuid

class Command(BaseCommand):
    help = 'Test all system emails (Welcome, Payment Receipt)'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Recipient email address')

    def handle(self, *args, **options):
        recipient_email = options['email']
        self.stdout.write(f"Starting email test for {recipient_email}...")

        # Find or create a test user
        user, created = User.objects.get_or_create(
            email=recipient_email,
            defaults={'username': f"testuser_{uuid.uuid4().hex[:8]}", 'is_email_verified': True}
        )
        if created:
            self.stdout.write(f"Created temporary test user: {user.username}")
        else:
            # Ensure they are verified so welcome email trigger works if we were using signals,
            # but here we call it directly.
            user.is_email_verified = True
            user.save()

        # 1. Test Welcome Email
        self.stdout.write("Sending Welcome Email...")
        try:
            send_welcome_email(user)
            self.stdout.write(self.style.SUCCESS("✅ Welcome Email sent!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Welcome Email failed: {str(e)}"))

        # 2. Test Payment Receipt Email
        # Find a successful payment for this user, or create a mock one
        payment = Payment.objects.filter(user=user, status='success').first()
        if not payment:
            self.stdout.write("No existing success payment found for user, creating a mock one...")
            payment = Payment.objects.create(
                user=user,
                amount=29.99,
                currency='USD',
                status='success',
                payment_type='subscription',
                razorpay_payment_id='pay_test_' + uuid.uuid4().hex[:10]
            )
            # Invoice number is generated in save() override or by calling _generate_invoice_number
            payment._generate_invoice_number()
            payment.save()

        self.stdout.write(f"Sending Payment Receipt Email for Payment {payment.id}...")
        try:
            # We call the service directly to bypass Celery for immediate testing
            result = EmailService.send_payment_receipt(str(payment.id))
            if result.get('success'):
                self.stdout.write(self.style.SUCCESS("✅ Payment Receipt Email sent (with PDF attachment)!"))
            else:
                self.stdout.write(self.style.ERROR(f"❌ Payment Receipt Email failed: {result.get('error')}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Payment Receipt Email failed: {str(e)}"))

        self.stdout.write(self.style.SUCCESS("\nEmail test sequence complete. Check your inbox!"))
