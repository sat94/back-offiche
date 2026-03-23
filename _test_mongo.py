import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'back_office.settings')
django.setup()

from django.conf import settings
print("=== SSH Tunnel Ports ===")
print(f"PG_LOCAL_PORT: {settings.PG_LOCAL_PORT if hasattr(settings, 'PG_LOCAL_PORT') else 'N/A'}")
print(f"MONGO_GATEWAY_PORT: {settings.MONGO_GATEWAY_PORT if hasattr(settings, 'MONGO_GATEWAY_PORT') else 'N/A'}")
print(f"MONGO_API_PORT: {settings.MONGO_API_PORT if hasattr(settings, 'MONGO_API_PORT') else 'N/A'}")

print("\n=== MONGO URIs ===")
for key, uri in settings.MONGO_DATABASES.items():
    masked = uri[:30] + '...' if len(uri) > 30 else uri
    print(f"  {key}: {masked}")

print("\n=== Testing connections ===")
from back_office.mongodb import get_all_mongo_connections
results = get_all_mongo_connections()
for key, info in results.items():
    print(f"  {key}: {info}")
