from django.test import TestCase
from django.db import connections
from django.conf import settings
from pymongo import MongoClient


class PostgreSQLConnectionTest(TestCase):
    def test_default_connection(self):
        conn = connections['default']
        conn.ensure_connection()
        self.assertFalse(conn.connection is None)

    def test_can_query_tables(self):
        conn = connections['default']
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            tables = [row[0] for row in cursor.fetchall()]
        self.assertGreater(len(tables), 0)

    def test_compte_table_exists(self):
        conn = connections['default']
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'compte_compte'
                )
            """)
            exists = cursor.fetchone()[0]
        self.assertTrue(exists)

    def test_can_count_comptes(self):
        conn = connections['default']
        with conn.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM compte_compte')
            count = cursor.fetchone()[0]
        self.assertIsInstance(count, int)

    def test_plan_abonnement_table_exists(self):
        conn = connections['default']
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'plan_abonnement'
                )
            """)
            exists = cursor.fetchone()[0]
        self.assertTrue(exists)

    def test_facture_table_exists(self):
        conn = connections['default']
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'facture'
                )
            """)
            exists = cursor.fetchone()[0]
        self.assertTrue(exists)


class MongoGatewayConnectionTest(TestCase):
    def setUp(self):
        uri = settings.MONGO_DATABASES.get('gateway', '')
        if not uri:
            self.skipTest('MONGO_GATEWAY_URI not configured')
        self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)

    def tearDown(self):
        if hasattr(self, 'client'):
            self.client.close()

    def test_connection(self):
        self.client.admin.command('ping')

    def test_database_exists(self):
        db = self.client.get_default_database()
        self.assertIsNotNone(db)
        self.assertEqual(db.name, 'meetvoice_gateway')

    def test_list_collections(self):
        db = self.client.get_default_database()
        collections = db.list_collection_names()
        self.assertIsInstance(collections, list)


class MongoAPIConnectionTest(TestCase):
    def setUp(self):
        uri = settings.MONGO_DATABASES.get('api', '')
        if not uri:
            self.skipTest('MONGO_API_URI not configured')
        self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)

    def tearDown(self):
        if hasattr(self, 'client'):
            self.client.close()

    def test_connection(self):
        self.client.admin.command('ping')

    def test_database_exists(self):
        db = self.client.get_default_database()
        self.assertIsNotNone(db)
        self.assertEqual(db.name, 'meetvoice_api')

    def test_list_collections(self):
        db = self.client.get_default_database()
        collections = db.list_collection_names()
        self.assertIsInstance(collections, list)


class MongoGateway2ConnectionTest(TestCase):
    def setUp(self):
        uri = settings.MONGO_DATABASES.get('gateway2', '')
        if not uri:
            self.skipTest('MONGO_GATEWAY2_URI not configured')
        self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)

    def tearDown(self):
        if hasattr(self, 'client'):
            self.client.close()

    def test_connection(self):
        self.client.admin.command('ping')

    def test_database_exists(self):
        db = self.client.get_default_database()
        self.assertIsNotNone(db)
        self.assertEqual(db.name, 'meetvoice_gateway')

    def test_list_collections(self):
        db = self.client.get_default_database()
        collections = db.list_collection_names()
        self.assertIsInstance(collections, list)


class MongoSocialConnectionTest(TestCase):
    def setUp(self):
        uri = settings.MONGO_DATABASES.get('social', '')
        if not uri:
            self.skipTest('MONGO_SOCIAL_URI not configured')
        self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)

    def tearDown(self):
        if hasattr(self, 'client'):
            self.client.close()

    def test_connection(self):
        self.client.admin.command('ping')

    def test_database_exists(self):
        db = self.client.get_default_database()
        self.assertIsNotNone(db)
        self.assertEqual(db.name, 'meetvoice_social')

    def test_list_collections(self):
        db = self.client.get_default_database()
        collections = db.list_collection_names()
        self.assertIsInstance(collections, list)
