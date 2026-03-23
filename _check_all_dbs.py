import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'back_office.settings')
django.setup()

from back_office.mongodb import get_mongo_database

dbs = ['gateway', 'api', 'gateway2', 'social']

for key in dbs:
    try:
        db = get_mongo_database(key)
        cols = db.list_collection_names()
        total = sum(db[c].count_documents({}) for c in cols)
        if cols:
            print(f'\n[{key}] {len(cols)} collections, {total} docs total')
            for c in sorted(cols):
                n = db[c].count_documents({})
                print(f'  {c}: {n} docs' if n else f'  {c}: (vide)')
        else:
            print(f'\n[{key}] BASE VIDE')
    except Exception as e:
        print(f'\n[{key}] ERREUR: {e}')
