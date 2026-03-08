import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def add_columns():
    with connection.cursor() as cursor:
        try:
            cursor.execute("ALTER TABLE automation_triggers ADD COLUMN queued_at datetime")
            print("Successfully added queued_at to automation_triggers")
        except Exception as e:
            print(f"Error adding queued_at: {e}")
            
        try:
            cursor.execute("ALTER TABLE automation_triggers ADD COLUMN error_message TEXT DEFAULT ''")
            print("Successfully added error_message to automation_triggers")
        except Exception as e:
            print(f"Error adding error_message: {e}")

if __name__ == "__main__":
    add_columns()
