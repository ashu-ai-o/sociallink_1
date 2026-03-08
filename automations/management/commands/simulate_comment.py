"""
Management command: simulate_comment

Simulates a real Instagram webhook comment event hitting your local server.
Useful for testing the full automation pipeline without needing real Instagram comments.

Usage:
    python manage.py simulate_comment
    python manage.py simulate_comment --text "test1" --username the_raconz
    python manage.py simulate_comment --text "hello" --user-id 123456789
    python manage.py simulate_comment --list-automations
"""

import requests
import json
import hmac
import hashlib
import time
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Simulate an Instagram comment webhook to test the full automation pipeline locally'

    def add_arguments(self, parser):
        parser.add_argument(
            '--text',
            type=str,
            default='test1',
            help='Comment text to simulate (default: test1)',
        )
        parser.add_argument(
            '--username',
            type=str,
            default='the_raconz',
            help='Username of the commenter (default: the_raconz)',
        )
        parser.add_argument(
            '--user-id',
            type=str,
            default='26159303547039775',  # the_raconz's real Instagram user ID
            help='Instagram user ID of the commenter',
        )
        parser.add_argument(
            '--account',
            type=str,
            default=None,
            help='Instagram account username to trigger automation for (default: first active account)',
        )
        parser.add_argument(
            '--list-automations',
            action='store_true',
            help='List all active automations and exit',
        )

    def handle(self, *args, **options):
        from automations.models import InstagramAccount, Automation, AutomationTrigger

        # --- List automations ---
        if options['list_automations']:
            self.stdout.write('\n--- Active Automations ---')
            for a in Automation.objects.filter(is_active=True).select_related('instagram_account'):
                self.stdout.write(
                    f'  [{a.id}] "{a.name}" | '
                    f'account=@{a.instagram_account.username} | '
                    f'keywords={a.trigger_keywords} | '
                    f'match={a.trigger_match_type} | '
                    f'posts={a.target_posts}'
                )
            return

        # --- Resolve Instagram account ---
        if options['account']:
            account = InstagramAccount.objects.filter(
                username=options['account'], is_active=True
            ).first()
        else:
            account = InstagramAccount.objects.filter(is_active=True).first()

        if not account:
            self.stderr.write(self.style.ERROR('No active Instagram account found. Connect one first.'))
            return

        ig_user_id = account.platform_id or account.instagram_user_id

        # Find an available post ID from active automations
        automation = Automation.objects.filter(
            instagram_account=account, is_active=True, trigger_type='comment'
        ).first()

        if not automation:
            self.stderr.write(self.style.ERROR(
                f'No active comment automation found for @{account.username}. '
                f'Create one first.'
            ))
            return

        post_id = (
            automation.target_posts[0]
            if automation.target_posts
            else '000000000000000'
        )

        start_time = time.time()

        self.stdout.write(f'\n--- Simulating Comment Webhook ---')
        self.stdout.write(f'  Account:    @{account.username} (id={ig_user_id})')
        self.stdout.write(f'  Post:       {post_id}')
        self.stdout.write(f'  Commenter:  @{options["username"]} (id={options["user_id"]})')
        self.stdout.write(f'  Text:       "{options["text"]}"')
        self.stdout.write(f'  Automation: "{automation.name}"')
        self.stdout.write(f'  Keywords:   {automation.trigger_keywords} ({automation.trigger_match_type})')
        self.stdout.write('')

        # Build Meta-format webhook payload
        # NOTE: We do NOT set a comment_id in simulated events.
        # Using a fake comment_id like SIMULATED_xxx causes a 400 because Instagram
        # can't find that comment. Instead, the DM will use user_id directly.
        payload = {
            'object': 'instagram',
            'entry': [{
                'id': ig_user_id,
                'time': int(time.time()),
                'changes': [{
                    'field': 'comments',
                    'value': {
                        'from': {
                            'id': options['user_id'],
                            'username': options['username'],
                        },
                        'media': {
                            'id': post_id,
                            'media_product_type': 'FEED'
                        },
                        # No 'id' (comment_id) intentionally — forces DM to use user_id
                        'text': options['text'],
                        'timestamp': int(time.time()),
                    }
                }]
            }]
        }

        body = json.dumps(payload).encode('utf-8')

        # Sign with FACEBOOK_APP_SECRET (same as Meta signs real webhooks)
        secret = settings.FACEBOOK_APP_SECRET
        sig = 'sha256=' + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

        # Send to local server
        try:
            r = requests.post(
                'http://127.0.0.1:8000/api/webhooks/instagram/',
                data=body,
                headers={
                    'Content-Type': 'application/json',
                    'X-Hub-Signature-256': sig,
                },
                timeout=10,
            )
            if r.ok:
                self.stdout.write(self.style.SUCCESS(f'[OK] Webhook delivered: {r.status_code} {r.text}'))
            else:
                self.stderr.write(self.style.ERROR(f'[FAIL] Webhook failed: {r.status_code} {r.text}'))
                return
        except requests.ConnectionError:
            self.stderr.write(self.style.ERROR(
                'Could not connect to http://127.0.0.1:8000. Is Django running? '
                '(python manage.py runserver)'
            ))
            return

        # Wait for Celery to process the trigger
        from django.utils import timezone as tz
        import datetime
        self.stdout.write('Waiting for Celery to process the trigger...')
        since = tz.now() - datetime.timedelta(seconds=5)
        trigger = None
        for i in range(8):  # wait up to 16 seconds
            time.sleep(2)
            trigger = AutomationTrigger.objects.filter(
                instagram_user_id=options['user_id'],
                created_at__gte=since
            ).order_by('-created_at').first()
            if not trigger:
                if i == 7:
                    self.stdout.write(self.style.WARNING(
                        'No trigger created. The comment may have been filtered out:\n'
                        '  - Text did not match automation keywords\n'
                        '  - Post ID not in automation target_posts\n'
                        'Check Django server logs for [FILTER] messages.'
                    ))
                continue

            self.stdout.write(f'  Trigger status: {trigger.status}')

            if trigger.status == 'sent':
                self.stdout.write(self.style.SUCCESS(
                    f'\n[SUCCESS] Full pipeline worked!\n'
                    f'  DM sent at: {trigger.dm_sent_at}\n'
                    f'  Comment reply: {trigger.comment_reply_sent}\n'
                    f'  Message: "{trigger.DmMessage_sent}"'
                ))
                return
            elif trigger.status == 'failed':
                err = trigger.error_message or 'unknown'
                self.stdout.write(self.style.ERROR(
                    f'\n[FAILED] {err[:300]}'
                ))
                self.stdout.write(
                    'Cause: To DM someone via user_id (simulation), they must have\n'
                    'messaged @wanderwithraconz first. For a REAL end-to-end test:\n'
                    '  Have @the_raconz comment "test1" on the post directly\n'
                    '  (webhook fires with real comment_id -> DM works)'
                )
                return
            elif trigger.status == 'skipped':
                self.stdout.write(self.style.WARNING(f'[SKIPPED] {trigger.error_message}'))
                return

        self.stdout.write(self.style.WARNING(
            '[TIMEOUT] Celery did not process the trigger in time.\n'
            'Check that Celery worker is running: celery -A core worker --pool=solo -l info'
        ))
```
