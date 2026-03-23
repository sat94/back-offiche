import os, django, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'back_office.settings')
django.setup()
from back_office.mongodb import get_mongo_database

db = get_mongo_database('api')

print("=== posts (1 sample) ===")
doc = db['posts'].find_one()
if doc:
    for k, v in doc.items():
        print(f"  {k}: {type(v).__name__} = {str(v)[:100]}")
print()

print("=== post_comments (1 sample) ===")
doc = db['post_comments'].find_one()
if doc:
    for k, v in doc.items():
        print(f"  {k}: {type(v).__name__} = {str(v)[:100]}")
print()

print("=== reply_likes (1 sample) ===")
doc = db['reply_likes'].find_one()
if doc:
    for k, v in doc.items():
        print(f"  {k}: {type(v).__name__} = {str(v)[:100]}")
print()

print("=== counts ===")
print(f"  posts: {db['posts'].count_documents({})}")
print(f"  post_comments: {db['post_comments'].count_documents({})}")
print(f"  reply_likes: {db['reply_likes'].count_documents({})}")
print(f"  post_likes: {db['post_likes'].count_documents({})}")
print(f"  comment_likes: {db['comment_likes'].count_documents({})}")

print("\n=== posts (3 samples) ===")
for doc in db['posts'].find().sort('_id', -1).limit(3):
    doc['_id'] = str(doc['_id'])
    for k, v in doc.items():
        if hasattr(v, 'isoformat'):
            doc[k] = v.isoformat()
    print(json.dumps(doc, default=str, indent=2))
    print("---")

print("\n=== post_comments (3 samples) ===")
for doc in db['post_comments'].find().sort('_id', -1).limit(3):
    doc['_id'] = str(doc['_id'])
    for k, v in doc.items():
        if hasattr(v, 'isoformat'):
            doc[k] = v.isoformat()
    print(json.dumps(doc, default=str, indent=2))
    print("---")
