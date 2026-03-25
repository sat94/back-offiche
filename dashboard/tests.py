import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import connections
from django.conf import settings
from pymongo import MongoClient

from core.models import UserEvent


class PostgreSQLConnectionTest(TestCase):
    databases = ['default']

    def test_default_connection(self):
        conn = connections['default']
        conn.ensure_connection()
        self.assertIsNotNone(conn.connection)

    def test_can_query_tables(self):
        conn = connections['default']
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            )
            tables = [row[0] for row in cursor.fetchall()]
        self.assertGreater(len(tables), 0)

    def test_compte_table_exists(self):
        conn = connections['default']
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = 'compte_compte')"
            )
            self.assertTrue(cursor.fetchone()[0])

    def test_can_count_comptes(self):
        conn = connections['default']
        with conn.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM compte_compte')
            count = cursor.fetchone()[0]
        self.assertIsInstance(count, int)
        self.assertGreaterEqual(count, 0)

    def test_plan_abonnement_table_exists(self):
        conn = connections['default']
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = 'plan_abonnement')"
            )
            self.assertTrue(cursor.fetchone()[0])

    def test_facture_table_exists(self):
        conn = connections['default']
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = 'facture')"
            )
            self.assertTrue(cursor.fetchone()[0])

    def test_tracking_user_event_table_exists(self):
        conn = connections['default']
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = 'tracking_user_event')"
            )
            self.assertTrue(cursor.fetchone()[0])


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
        self.assertIsInstance(db.list_collection_names(), list)


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
        self.assertIsInstance(db.list_collection_names(), list)


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
        self.assertIsInstance(db.list_collection_names(), list)


class TrackingEventTest(TestCase):
    databases = ['default']

    def setUp(self):
        self.client = Client()

    def test_tracking_event_post_valid(self):
        payload = {
            'session_id': 'test-session-abc123',
            'event_type': 'registration_step',
            'step': 2,
            'step_name': 'sexe',
        }
        response = self.client.post(
            '/tracking/event/',
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('ok'))

    def test_tracking_event_creates_model(self):
        before = UserEvent.objects.count()
        payload = {
            'session_id': 'test-session-xyz789',
            'event_type': 'registration_complete',
            'step': 8,
            'step_name': 'complete',
            'compte_id': 'some-uuid-here',
        }
        self.client.post(
            '/tracking/event/',
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(UserEvent.objects.count(), before + 1)

    def test_tracking_event_cors_headers(self):
        response = self.client.options('/tracking/event/')
        self.assertEqual(response.get('Access-Control-Allow-Origin'), '*')

    def test_tracking_event_rejects_get(self):
        response = self.client.get('/tracking/event/')
        self.assertEqual(response.status_code, 405)

    def test_tracking_event_invalid_json(self):
        response = self.client.post(
            '/tracking/event/',
            data='not-json',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_tracking_event_ip_captured(self):
        payload = {
            'session_id': 'ip-test-session',
            'event_type': 'page_view',
        }
        self.client.post(
            '/tracking/event/',
            data=json.dumps(payload),
            content_type='application/json',
            REMOTE_ADDR='1.2.3.4',
        )
        ev = UserEvent.objects.filter(session_id='ip-test-session').last()
        self.assertIsNotNone(ev)
        self.assertEqual(ev.ip_address, '1.2.3.4')


class UserEventModelTest(TestCase):
    databases = ['default']

    def test_create_user_event(self):
        ev = UserEvent.objects.create(
            session_id='model-test-session',
            event_type='registration_step',
            step=3,
            step_name='age',
        )
        self.assertIsNotNone(ev.pk)
        self.assertEqual(ev.step, 3)
        self.assertEqual(ev.step_name, 'age')

    def test_user_event_str(self):
        ev = UserEvent(
            session_id='abcdefgh1234',
            event_type='registration_complete',
            step=8,
        )
        result = str(ev)
        self.assertIn('registration_complete', result)
        self.assertIn('abcdefg', result)

    def test_user_event_data_json(self):
        ev = UserEvent.objects.create(
            session_id='json-test-session',
            event_type='page_view',
            data={'page': 'landing', 'ref': 'google'},
        )
        ev.refresh_from_db()
        self.assertEqual(ev.data['page'], 'landing')
        self.assertEqual(ev.data['ref'], 'google')


class DashboardViewsTest(TestCase):
    databases = ['default']

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testadmin',
            password='testpass123',
        )

    def test_login_required_redirects(self):
        protected_urls = [
            '/user-tracking/',
            '/user-tracking/api/',
        ]
        for url in protected_urls:
            resp = self.client.get(url)
            self.assertIn(resp.status_code, [301, 302], msg=f'{url} should redirect')

    def test_user_tracking_page_authenticated(self):
        self.client.login(username='testadmin', password='testpass123')
        resp = self.client.get('/user-tracking/')
        self.assertEqual(resp.status_code, 200)

    def test_user_tracking_api_authenticated(self):
        self.client.login(username='testadmin', password='testpass123')
        resp = self.client.get('/user-tracking/api/?days=7&exclude_admin=1')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('stats', data)
        self.assertIn('funnel', data)
        self.assertIn('retention', data)

    def test_user_tracking_api_stats_structure(self):
        self.client.login(username='testadmin', password='testpass123')
        resp = self.client.get('/user-tracking/api/?section=stats&days=30')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        stats = data.get('stats', {})
        self.assertIn('total', stats)
        self.assertIn('new_7d', stats)
        self.assertIn('new_30d', stats)
        self.assertIn('verified', stats)
        self.assertIn('premium', stats)
        self.assertIsInstance(stats['total'], int)

    def test_user_tracking_api_funnel_structure(self):
        self.client.login(username='testadmin', password='testpass123')
        resp = self.client.get('/user-tracking/api/?section=funnel&days=30')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        funnel = data.get('funnel', [])
        self.assertIsInstance(funnel, list)
        self.assertEqual(len(funnel), 8)
        for step in funnel:
            self.assertIn('step', step)
            self.assertIn('count', step)
            self.assertIn('pct', step)

    def test_user_tracking_api_bot_detection(self):
        self.client.login(username='testadmin', password='testpass123')
        resp = self.client.get('/user-tracking/api/?section=bots&days=30')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('bot_ips', data)
        self.assertIn('ip_multi_accounts', data)
        self.assertIsInstance(data['bot_ips'], list)
        self.assertIsInstance(data['ip_multi_accounts'], list)

    def test_user_tracking_api_unauthenticated(self):
        resp = self.client.get('/user-tracking/api/')
        self.assertIn(resp.status_code, [301, 302])
