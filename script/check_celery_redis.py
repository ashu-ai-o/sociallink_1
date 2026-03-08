import os
import django
from core.celery import app
import redis

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def check_redis():
    print("--- Checking Redis ---")
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        print('Redis Ping:', r.ping())
        print('Queued items in celery:', r.llen('celery'))
    except Exception as e:
        print('Redis Connection Error:', e)

def check_celery():
    print("\n--- Checking Celery ---")
    try:
        i = app.control.inspect()
        active = i.active()
        if active is None:
            print("No Celery workers running.")
        else:
            print("Active workers:", list(active.keys()))
            for worker, tasks in active.items():
                print(f"[{worker}] Active tasks:", len(tasks))
                
        reserved = i.reserved()
        if reserved:
            for worker, tasks in reserved.items():
                print(f"[{worker}] Reserved/Pending tasks:", len(tasks))
    except Exception as e:
        print("Celery inspection error:", e)

if __name__ == '__main__':
    check_redis()
    check_celery()
