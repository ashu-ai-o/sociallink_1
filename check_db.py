import sqlite3

def check_db():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in db.sqlite3:")
    for table in tables:
        print(f" - {table[0]}")
    
    # Check django_migrations
    print("\nApplied Migrations:")
    cursor.execute("SELECT app, name FROM django_migrations ORDER BY app, name;")
    migrations = cursor.fetchall()
    for m in migrations:
        print(f" - {m[0]}: {m[1]}")
    
    conn.close()

if __name__ == '__main__':
    check_db()
