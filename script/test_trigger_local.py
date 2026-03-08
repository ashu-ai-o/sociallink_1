import os
import django
import asyncio

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from automations.tasks import _check_comments_async

def main():
    asyncio.run(_check_comments_async())

if __name__ == '__main__':
    main()
