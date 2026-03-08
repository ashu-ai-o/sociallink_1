"""
Management command: setup_webhook

Usage:
    python manage.py setup_webhook                   # Auto-detect ngrok URL
    python manage.py setup_webhook --url https://x.ngrok.io  # Use specific URL
    python manage.py setup_webhook --check           # Just show current subscription

What it does:
1. Reads the current ngrok public URL from ngrok local API (port 4040)
2. Registers/updates the Meta app webhook subscription (comments + messages)
3. Re-subscribes all active Instagram accounts to push events to the webhook

Run this every time you restart ngrok.
"""

import requests
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Register / refresh the Instagram webhook URL (run after each ngrok restart)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            default=None,
            help='Override backend URL (e.g. https://abc123.ngrok-free.app). '
                 'If omitted, auto-detected from ngrok local API.',
        )
        parser.add_argument(
            '--check',
            action='store_true',
            help='Only display the current webhook subscription — no changes made.',
        )

    def handle(self, *args, **options):
        check_only = options['check']
        manual_url = options['url']

        # --- Step 1: Resolve backend URL ---
        if manual_url:
            backend_url = manual_url.rstrip('/')
            self.stdout.write('  Using provided URL: ' + backend_url)
        else:
            backend_url = self._detect_ngrok_url()
            if not backend_url:
                backend_url = getattr(settings, 'BACKEND_URL', '').rstrip('/')
                if not backend_url:
                    self.stderr.write(self.style.ERROR(
                        'Could not detect ngrok URL and BACKEND_URL is not set. '
                        'Start ngrok or pass --url.'
                    ))
                    return
                self.stdout.write('  ngrok not detected, using BACKEND_URL from settings: ' + backend_url)
            else:
                self.stdout.write(self.style.SUCCESS('  Detected ngrok URL: ' + backend_url))

        webhook_url = backend_url + '/api/webhooks/instagram/'
        verify_token = getattr(settings, 'INSTAGRAM_WEBHOOK_VERIFY_TOKEN', '')
        fb_app_id = getattr(settings, 'FACEBOOK_APP_ID', '')
        fb_app_secret = getattr(settings, 'FACEBOOK_APP_SECRET', '')

        if not all([verify_token, fb_app_id, fb_app_secret]):
            self.stderr.write(self.style.ERROR(
                'Missing required settings: INSTAGRAM_WEBHOOK_VERIFY_TOKEN, '
                'FACEBOOK_APP_ID, FACEBOOK_APP_SECRET'
            ))
            return

        app_access_token = fb_app_id + '|' + fb_app_secret

        # --- Step 2: Check existing subscription ---
        self.stdout.write('\n--- Current Webhook Subscription ---')
        self._check_subscription(fb_app_id, app_access_token)

        if check_only:
            return

        # --- Step 3: Register / update the webhook subscription ---
        self.stdout.write('\n--- Registering Webhook ---')
        self.stdout.write('  Callback URL : ' + webhook_url)
        self.stdout.write('  Fields       : comments, messages')

        sub_url = 'https://graph.facebook.com/v25.0/' + fb_app_id + '/subscriptions'
        resp = requests.post(sub_url, data={
            'object': 'instagram',
            'callback_url': webhook_url,
            'fields': 'comments,messages',
            'verify_token': verify_token,
            'access_token': app_access_token,
        })
        if resp.ok and resp.json().get('success'):
            self.stdout.write(self.style.SUCCESS('  [OK] Subscribed to instagram webhooks'))
        else:
            self.stderr.write(self.style.WARNING(
                '  [FAIL] Subscription failed: ' + str(resp.status_code) + ' ' + resp.text
            ))

        # --- Step 4: Re-subscribe each active Instagram account ---
        self.stdout.write('\n--- Re-subscribing Instagram Accounts ---')
        self._resubscribe_accounts()

        # --- Step 5: Show final state ---
        self.stdout.write('\n--- Updated Subscription ---')
        self._check_subscription(fb_app_id, app_access_token)
        self.stdout.write(self.style.SUCCESS(
            '\n[DONE] Webhooks now pointing to: ' + webhook_url + '\n'
            'Also update this URL in Meta App Dashboard > Webhooks if it changed.'
        ))

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _detect_ngrok_url(self):
        """Try to read the current tunnel URL from ngrok local API."""
        try:
            resp = requests.get('http://127.0.0.1:4040/api/tunnels', timeout=3)
            resp.raise_for_status()
            tunnels = resp.json().get('tunnels', [])
            for tunnel in tunnels:
                if tunnel.get('proto') == 'https':
                    return tunnel['public_url'].rstrip('/')
            if tunnels:
                return tunnels[0]['public_url'].rstrip('/')
        except Exception:
            pass
        return None

    def _check_subscription(self, fb_app_id, app_access_token):
        """Display the app's current webhook subscriptions."""
        resp = requests.get(
            'https://graph.facebook.com/v25.0/' + fb_app_id + '/subscriptions',
            params={'access_token': app_access_token}
        )
        if not resp.ok:
            self.stderr.write('  Could not fetch: ' + str(resp.status_code) + ' ' + resp.text)
            return

        subs = resp.json().get('data', [])
        if not subs:
            self.stdout.write('  No webhook subscriptions found.')
            return

        for sub in subs:
            self.stdout.write(
                '  object=' + str(sub.get('object')) +
                ' | callback_url=' + str(sub.get('callback_url')) +
                ' | fields=' + str(sub.get('fields')) +
                ' | active=' + str(sub.get('active'))
            )

    def _resubscribe_accounts(self):
        """Re-subscribe all active Instagram accounts to webhook fields."""
        from automations.models import InstagramAccount

        accounts = InstagramAccount.objects.filter(is_active=True)
        if not accounts.exists():
            self.stdout.write('  No active Instagram accounts found.')
            return

        for account in accounts:
            if account.connection_method == 'instagram_platform':
                user_id = account.platform_id or account.instagram_user_id
                url = 'https://graph.instagram.com/v25.0/' + user_id + '/subscribed_apps'
            else:
                if not account.page_id:
                    self.stdout.write('  [SKIP] @' + account.username + ': no page_id')
                    continue
                url = 'https://graph.facebook.com/v25.0/' + account.page_id + '/subscribed_apps'

            resp = requests.post(url, params={
                'subscribed_fields': 'comments,messages',
                'access_token': account.access_token,
            })

            if resp.ok and resp.json().get('success'):
                self.stdout.write(self.style.SUCCESS(
                    '  [OK] @' + account.username + ' subscribed (' + account.connection_method + ')'
                ))
            else:
                self.stderr.write(self.style.WARNING(
                    '  [FAIL] @' + account.username + ': ' + str(resp.status_code) + ' ' + resp.text
                ))
