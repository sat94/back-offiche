"""
Tests de performance / charge — MeetVoice Back Office
Simule des requêtes simultanées sur les endpoints critiques et mesure :
  - Taux de succès (toutes les requêtes doivent répondre 200)
  - Temps de réponse moyen / max / p95
  - Efficacité du cache (2e requête plus rapide que la 1re)
  - Solidité sous charge (N requêtes simultanées)
"""
import json
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.core.cache import cache

from core.models import UserEvent


CONCURRENT_USERS = 20
MAX_AVG_RESPONSE_MS = 3000
MAX_P95_RESPONSE_MS = 6000
MAX_SINGLE_RESPONSE_MS = 5000


@override_settings(SESSION_ENGINE='django.contrib.sessions.backends.db')
class UserTrackingAPILoadTest(TestCase):
    """
    Endpoint /user-tracking/api/ : chargé à chaque refresh du dashboard admin.
    Vérifie temps de réponse et efficacité du cache.
    """
    databases = ['default']

    def setUp(self):
        self.user = User.objects.create_user(
            username='perfadmin_load', password='perfpass123!'
        )
        self.auth_client = Client()
        ok = self.auth_client.login(username='perfadmin_load', password='perfpass123!')
        self.assertTrue(ok, 'Login failed in setUp')
        cache.clear()

    def test_single_request_response_time(self):
        """Une seule requête full (section=all) doit répondre en moins de {MAX}ms."""
        start = time.perf_counter()
        resp = self.auth_client.get('/user-tracking/api/?section=all&days=30')
        elapsed_ms = (time.perf_counter() - start) * 1000

        self.assertEqual(resp.status_code, 200)
        self.assertLess(
            elapsed_ms, MAX_SINGLE_RESPONSE_MS,
            f'Première requête trop lente : {elapsed_ms:.0f}ms (max: {MAX_SINGLE_RESPONSE_MS}ms)'
        )

    def test_cache_accelerates_second_request(self):
        """La 2e requête identique doit être plus rapide grâce au cache."""
        url = '/user-tracking/api/?section=all&days=30&exclude_admin=1'

        start1 = time.perf_counter()
        resp1 = self.auth_client.get(url)
        t1 = (time.perf_counter() - start1) * 1000
        self.assertEqual(resp1.status_code, 200)

        start2 = time.perf_counter()
        resp2 = self.auth_client.get(url)
        t2 = (time.perf_counter() - start2) * 1000
        self.assertEqual(resp2.status_code, 200)

        self.assertLess(
            t2, t1,
            f'Cache inactif : 1re={t1:.0f}ms, 2e={t2:.0f}ms — la 2e devrait être plus rapide'
        )

    def test_repeated_requests_stable(self):
        """10 requêtes successives : toutes doivent répondre 200 sans dégradation."""
        times = []
        for _ in range(10):
            start = time.perf_counter()
            resp = self.auth_client.get('/user-tracking/api/?section=stats&days=30')
            times.append((time.perf_counter() - start) * 1000)
            self.assertEqual(resp.status_code, 200)

        avg = statistics.mean(times)
        self.assertLess(
            avg, MAX_AVG_RESPONSE_MS,
            f'Temps moyen dégradé : {avg:.0f}ms (max: {MAX_AVG_RESPONSE_MS}ms)'
        )

    def test_sections_all_respond(self):
        """Chaque section individuelle doit répondre 200 et contenir sa clé attendue."""
        sections = {
            'stats': 'stats',
            'funnel': 'funnel',
            'retention': 'retention',
            'daily': 'daily_signups',
            'bots': 'bot_ips',
            'fields': 'field_completion',
        }
        for section, expected_key in sections.items():
            resp = self.auth_client.get(f'/user-tracking/api/?section={section}&days=30')
            self.assertEqual(
                resp.status_code, 200,
                f'Section {section!r} a retourné {resp.status_code}'
            )
            data = resp.json()
            self.assertIn(
                expected_key, data,
                f'Section {section!r} ne contient pas la clé "{expected_key}"'
            )


class TrackingEndpointLoadTest(TestCase):
    """
    Endpoint /tracking/event/ : point chaud — reçoit un appel à chaque étape
    d'inscription de chaque visiteur sur meet-voice.fr.
    """
    databases = ['default']

    def setUp(self):
        self.client = Client()

    def _post_event(self, i, client=None):
        c = client or self.client
        payload = {
            'session_id': f'perf-session-{i:04d}',
            'event_type': 'registration_step',
            'step': (i % 7) + 1,
            'step_name': ['type', 'sexe', 'age', 'cgu', 'username', 'photo', 'email'][i % 7],
        }
        start = time.perf_counter()
        resp = c.post(
            '/tracking/event/',
            data=json.dumps(payload),
            content_type='application/json',
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        return resp.status_code, elapsed_ms

    def test_tracking_sequential_100_requests(self):
        """100 requêtes séquentielles — vérifie stabilité et temps de réponse."""
        times = []
        errors = 0
        for i in range(100):
            status, ms = self._post_event(i)
            times.append(ms)
            if status != 200:
                errors += 1

        avg = statistics.mean(times)
        p95 = sorted(times)[int(len(times) * 0.95)]

        self.assertEqual(errors, 0, f'{errors} requêtes ont échoué sur 100')
        self.assertLess(
            avg, MAX_AVG_RESPONSE_MS,
            f'Temps moyen trop élevé : {avg:.0f}ms (max: {MAX_AVG_RESPONSE_MS}ms)'
        )
        self.assertLess(
            p95, MAX_P95_RESPONSE_MS,
            f'P95 trop élevé : {p95:.0f}ms (max: {MAX_P95_RESPONSE_MS}ms)'
        )

    def test_tracking_concurrent_requests(self):
        """Simule {N} visiteurs qui envoient un event exactement en même temps."""
        results = []

        def worker(i):
            c = Client()
            return self._post_event(i, client=c)

        with ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
            futures = [executor.submit(worker, i) for i in range(CONCURRENT_USERS)]
            for f in as_completed(futures):
                results.append(f.result())

        errors = sum(1 for s, _ in results if s != 200)
        times = [t for _, t in results]
        avg = statistics.mean(times)

        self.assertEqual(errors, 0,
                         f'{errors}/{CONCURRENT_USERS} requêtes simultanées ont échoué')
        self.assertLess(
            avg, MAX_AVG_RESPONSE_MS * 2,
            f'Temps moyen sous charge trop élevé : {avg:.0f}ms'
        )

    def test_tracking_complete_inscription_flow(self):
        """Simule un flux complet (8 étapes) pour 10 sessions."""
        STEPS = [
            (1, 'type'), (2, 'sexe'), (3, 'age'), (4, 'cgu'),
            (5, 'username'), (6, 'photo'), (7, 'email'), (8, 'complete'),
        ]
        errors = 0
        for session_n in range(10):
            sid = f'flow-test-session-{session_n:03d}'
            for step_num, step_name in STEPS:
                event_type = 'registration_complete' if step_num == 8 else 'registration_step'
                payload = {
                    'session_id': sid,
                    'event_type': event_type,
                    'step': step_num,
                    'step_name': step_name,
                }
                resp = self.client.post(
                    '/tracking/event/',
                    data=json.dumps(payload),
                    content_type='application/json',
                )
                if resp.status_code != 200:
                    errors += 1

        self.assertEqual(errors, 0, f'{errors} events ont échoué dans le flux complet')

        sessions_complete = (
            UserEvent.objects
            .filter(session_id__startswith='flow-test-session-', event_type='registration_complete')
            .values('session_id').distinct().count()
        )
        self.assertEqual(sessions_complete, 10,
                         'Les 10 inscriptions complètes ne sont pas toutes enregistrées')


@override_settings(SESSION_ENGINE='django.contrib.sessions.backends.db')
class BotDetectionLoadTest(TestCase):
    """
    Vérifie que la détection de bots fonctionne correctement
    même quand une même IP envoie beaucoup de sessions.
    """
    databases = ['default']

    def setUp(self):
        self.track_client = Client()
        self.user = User.objects.create_user(username='botadmin_load', password='botpass123!')
        self.auth_client = Client()
        ok = self.auth_client.login(username='botadmin_load', password='botpass123!')
        self.assertTrue(ok, 'Login failed in setUp')

    def test_bot_ip_detected_after_many_sessions(self):
        """Une IP avec 5 sessions distinctes doit apparaître dans bot_ips."""
        bot_ip = '99.88.77.66'
        for i in range(5):
            payload = {
                'session_id': f'bot-session-{i:03d}',
                'event_type': 'registration_step',
                'step': 1,
                'step_name': 'type',
            }
            self.track_client.post(
                '/tracking/event/',
                data=json.dumps(payload),
                content_type='application/json',
                REMOTE_ADDR=bot_ip,
            )

        cache.clear()
        resp = self.auth_client.get('/user-tracking/api/?section=bots&days=1')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        bot_ips_list = [b['ip'] for b in data.get('bot_ips', [])]
        self.assertIn(bot_ip, bot_ips_list,
                      f'IP bot {bot_ip} non détectée (bot_ips: {bot_ips_list})')

    def test_multi_account_ip_detected(self):
        """Une IP avec 3 comptes complétés doit apparaître dans ip_multi_accounts."""
        multi_ip = '11.22.33.44'
        for i in range(3):
            payload = {
                'session_id': f'multi-acc-session-{i:03d}',
                'event_type': 'registration_complete',
                'step': 8,
                'step_name': 'complete',
                'compte_id': f'fake-compte-id-{i:03d}',
            }
            self.track_client.post(
                '/tracking/event/',
                data=json.dumps(payload),
                content_type='application/json',
                REMOTE_ADDR=multi_ip,
            )

        cache.clear()
        resp = self.auth_client.get('/user-tracking/api/?section=bots&days=1')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        multi_ips_list = [b['ip'] for b in data.get('ip_multi_accounts', [])]
        self.assertIn(multi_ip, multi_ips_list,
                      f'IP multi-comptes {multi_ip} non détectée')
