from pymongo import MongoClient
from django.conf import settings

_clients = {}


def get_mongo_client(db_key):
    if db_key not in _clients:
        uri = settings.MONGO_DATABASES.get(db_key, '')
        if not uri:
            raise ValueError(f"No MongoDB URI configured for '{db_key}'")
        _clients[db_key] = MongoClient(
            uri,
            serverSelectionTimeoutMS=2000,
            maxPoolSize=10,
            minPoolSize=1,
            maxIdleTimeMS=45000,
            connectTimeoutMS=5000,
            socketTimeoutMS=10000,
        )
    return _clients[db_key]


def get_mongo_database(db_key):
    client = get_mongo_client(db_key)
    return client.get_default_database()


def get_all_mongo_connections():
    results = {}
    for key, uri in settings.MONGO_DATABASES.items():
        if uri:
            try:
                client = get_mongo_client(key)
                db = client.get_default_database()
                client.admin.command('ping')
                results[key] = {
                    'status': 'connected',
                    'database': db.name,
                    'collections': db.list_collection_names(),
                }
            except Exception as e:
                results[key] = {'status': 'error', 'error': str(e)}
    return results


def close_all():
    for client in _clients.values():
        client.close()
    _clients.clear()
