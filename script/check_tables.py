import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection

def list_tables():
    tables = connection.introspection.table_names()
    print("Tables in database:")
    for table in sorted(tables):
        print(f"- {table}")

if __name__ == "__main__":
    list_tables()
