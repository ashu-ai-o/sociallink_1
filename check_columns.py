import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def check_columns(table_name):
    with connection.cursor() as cursor:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print(f"Columns in {table_name}:")
        for col in columns:
            print(f"- {col[1]} ({col[2]})")

if __name__ == "__main__":
    check_columns('automation_triggers')
