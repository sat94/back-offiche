import os, django, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'back_office.settings')
django.setup()
from back_office.mongodb import get_mongo_database

db = get_mongo_database('gateway')
print(f"messages count: {db['messages'].count_documents({})}")
print("\n=== messages (3 samples) ===")
for doc in db['messages'].find().sort('_id', -1).limit(3):
    doc['_id'] = str(doc['_id'])
    for k, v in doc.items():
        if hasattr(v, 'isoformat'):
            doc[k] = v.isoformat()
    print(json.dumps(doc, default=str, indent=2))
    print("---")

print("\n=== users (1 sample) ===")
doc = db['users'].find_one()
if doc:
    doc['_id'] = str(doc['_id'])
    for k, v in doc.items():
        if hasattr(v, 'isoformat'):
            doc[k] = v.isoformat()
    print(json.dumps(doc, default=str, indent=2))
