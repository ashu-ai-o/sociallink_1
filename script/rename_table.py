import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def rename_table():
    with connection.cursor() as cursor:
        try:
            cursor.execute("ALTER TABLE automations_automationvariant RENAME TO automation_variants")
            print("Successfully renamed automations_automationvariant to automation_variants")
        except Exception as e:
            print(f"Error renaming table: {e}")

if __name__ == "__main__":
    rename_table()
