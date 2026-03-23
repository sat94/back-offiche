import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'back_office.settings')
django.setup()

from django.db import connections

conn = connections['default']
with conn.cursor() as cursor:
    cursor.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' ORDER BY table_name
    """)
    all_tables = [row[0] for row in cursor.fetchall()]

    for t in all_tables:
        cursor.execute(f'SELECT COUNT(*) FROM "{t}"')
        count = cursor.fetchone()[0]
        print(f"{t}: {count}")
