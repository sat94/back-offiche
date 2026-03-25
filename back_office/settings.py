from pathlib import Path
from decouple import config
import atexit
import os
import socket
import threading
import time
import paramiko

BASE_DIR = Path(__file__).resolve().parent.parent

SSH_KEY_PATH = config('SSH_KEY_PATH', default=os.path.join(os.path.expanduser('~'), '.ssh', 'id_ed25519'))
SSH_USER = config('SSH_USER', default='root')

_cleanups = []
_tunnels = {}


def _find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def _port_is_alive(port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect(('127.0.0.1', port))
        s.close()
        return True
    except Exception:
        return False


def _start_ssh_tunnel(ssh_host, remote_host, remote_port, env_key, ssh_user=None):
    existing_port = os.environ.get(env_key, '').strip()
    if existing_port and existing_port.isdigit() and _port_is_alive(int(existing_port)):
        return int(existing_port)

    if existing_port:
        old_info = _tunnels.pop(env_key, None)
        if old_info:
            try:
                old_info['stop'].set()
                old_info['server'].close()
                old_info['client'].close()
            except Exception:
                pass

    local_port = _find_free_port()

    _user = ssh_user or SSH_USER

    def _connect():
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(ssh_host, username=_user, key_filename=SSH_KEY_PATH, timeout=15)
        t = c.get_transport()
        t.set_keepalive(15)
        return c, t

    client, transport = _connect()
    _tunnel_stop = threading.Event()
    _lock = threading.Lock()
    _state = {'client': client, 'transport': transport, 'fail_count': 0}

    def _reconnect():
        with _lock:
            try:
                _state['client'].close()
            except Exception:
                pass
            for attempt in range(5):
                if _tunnel_stop.is_set():
                    return False
                try:
                    c, t = _connect()
                    _state['client'] = c
                    _state['transport'] = t
                    _state['fail_count'] = 0
                    return True
                except Exception:
                    time.sleep(min(2 ** attempt, 30))
            _state['fail_count'] += 1
            return False

    def _get_transport():
        with _lock:
            t = _state['transport']
        try:
            if t and t.is_active():
                return t
        except Exception:
            pass
        if _reconnect():
            with _lock:
                return _state['transport']
        return None

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('127.0.0.1', local_port))
    server.listen(32)
    server.settimeout(1)

    def pipe(src, dst):
        try:
            while True:
                data = src.recv(65536)
                if not data:
                    break
                dst.sendall(data)
        except Exception:
            pass
        finally:
            for s in (src, dst):
                try:
                    s.close()
                except Exception:
                    pass

    def forward_loop():
        while not _tunnel_stop.is_set():
            try:
                local_conn, addr = server.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            t = _get_transport()
            if t is None:
                local_conn.close()
                continue

            try:
                remote_conn = t.open_channel('direct-tcpip', (remote_host, remote_port), addr)
            except Exception:
                local_conn.close()
                _reconnect()
                continue

            if remote_conn is None:
                local_conn.close()
                continue

            threading.Thread(target=pipe, args=(local_conn, remote_conn), daemon=True).start()
            threading.Thread(target=pipe, args=(remote_conn, local_conn), daemon=True).start()

    def health_check():
        while not _tunnel_stop.is_set():
            _tunnel_stop.wait(30)
            if _tunnel_stop.is_set():
                break
            _get_transport()

    threading.Thread(target=forward_loop, daemon=True).start()
    threading.Thread(target=health_check, daemon=True).start()

    def cleanup():
        _tunnel_stop.set()
        try:
            server.close()
        except Exception:
            pass
        try:
            _state['client'].close()
        except Exception:
            pass

    _tunnels[env_key] = {'stop': _tunnel_stop, 'server': server, 'client': _state['client']}
    _cleanups.append(cleanup)
    atexit.register(cleanup)
    os.environ[env_key] = str(local_port)
    return local_port


PG_LOCAL_PORT = _start_ssh_tunnel('81.17.103.146', 'localhost', 5432, '_SSH_PG_PORT')

MONGO_GATEWAY_PORT = _start_ssh_tunnel('164.68.109.146', 'localhost', 27017, '_SSH_MONGO_GW_PORT')

MONGO_API_PORT = _start_ssh_tunnel('164.68.115.49', 'localhost', 27017, '_SSH_MONGO_API_PORT')

PG_ARTICLE_PORT = _start_ssh_tunnel('149.102.143.243', 'localhost', 5432, '_SSH_PG_ARTICLE_PORT')

MONGO_EVENT_PORT = _start_ssh_tunnel('45.84.138.48', 'localhost', 27017, '_SSH_MONGO_EVENT_PORT')

_NE_SERVERS = [
    ('frontend', 'Frontend', '86.48.5.225', 'root'),
    ('backend', 'Backend', '156.67.29.190', 'root'),
    ('postgresql', 'PostgreSQL', '81.17.103.146', 'root'),
    ('mongo_messagerie', 'MongoDB Messagerie', '164.68.109.146', 'root'),
    ('mongo_reseaux', 'MongoDB Reseaux Sociaux', '164.68.115.49', 'root'),
    ('mongo_evenement', 'MongoDB Evenement', '45.84.138.48', 'root'),
    ('evenement', 'Evenement', '2.58.82.237', 'root'),
    ('ia', 'IA', '185.193.66.99', 'root'),
    ('automatisation', 'Automatisation', '149.102.143.243', 'root'),
    ('article', 'Article', '149.102.138.98', 'root'),
    ('reseaux_sociaux', 'Reseaux Sociaux', '62.171.154.23', 'root'),
    ('messagerie', 'Messagerie', '62.171.162.229', 'root'),
    ('websocket', 'WebSocket', '167.86.82.111', 'sulta'),
    ('gateway', 'Gateway', '89.117.49.9', 'root'),
]

MONITORING_TARGETS = {}
for _key, _label, _host, _user in _NE_SERVERS:
    _env_key = f'_SSH_NE_{_key.upper()}_PORT'
    try:
        _port = _start_ssh_tunnel(_host, 'localhost', 9100, _env_key, ssh_user=_user)
        MONITORING_TARGETS[_key] = {'label': f'{_label} ({_host})', 'local_port': _port}
    except Exception:
        pass


SECRET_KEY = config('SECRET_KEY', default='django-insecure-k=2qh+(0x!@i6&-slb2$#+kmo%!(k*t0c$ic&oem8z6np=^yk(')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'content',
    'compte',
    'dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'back_office.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
        },
    },
]

WSGI_APPLICATION = 'back_office.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('PG_MAIN_NAME', default='meetvoice_api'),
        'USER': config('PG_MAIN_USER', default='meetvoice_api_user'),
        'PASSWORD': config('PG_MAIN_PASSWORD', default=''),
        'HOST': '127.0.0.1',
        'PORT': str(PG_LOCAL_PORT),
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
        'TEST': {
            'NAME': config('PG_MAIN_NAME', default='meetvoice_api'),
        },
    },
    'articles': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'meetvoice',
        'USER': 'meetvoice',
        'PASSWORD': 'meetVoice123',
        'HOST': '127.0.0.1',
        'PORT': str(PG_ARTICLE_PORT),
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
    },
}

MONGO_DATABASES = {
    'gateway': f'mongodb://gateway_user:gateway_password_2025@127.0.0.1:{MONGO_GATEWAY_PORT}/meetvoice_gateway?authSource=admin',
    'api': f'mongodb://admin:Ilaaiua18aa45@127.0.0.1:{MONGO_API_PORT}/meetvoice_api?authSource=admin',
    'gateway2': f'mongodb://admin:Ilaaiua18aa45@127.0.0.1:{MONGO_API_PORT}/meetvoice_gateway?authSource=admin',
    'social': f'mongodb://admin:Ilaaiua18aa45@127.0.0.1:{MONGO_API_PORT}/meetvoice_social?authSource=admin',
    'event': f'mongodb://admin:AdminPass123!@127.0.0.1:{MONGO_EVENT_PORT}/admin?authSource=admin',
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

DATABASE_ROUTERS = ['content.db_router.ArticleRouter']

REDIS_URL = config('REDIS_URL', default='')

_redis_available = False
if REDIS_URL:
    try:
        import redis as _redis_lib
        _r = _redis_lib.from_url(REDIS_URL, socket_connect_timeout=2)
        _r.ping()
        _redis_available = True
    except Exception:
        pass

if _redis_available:
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'TIMEOUT': 300,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'SOCKET_CONNECT_TIMEOUT': 5,
                'SOCKET_TIMEOUT': 5,
                'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
                'IGNORE_EXCEPTIONS': True,
            },
            'KEY_PREFIX': 'bo',
        }
    }
else:
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'TIMEOUT': 300,
            'OPTIONS': {
                'MAX_ENTRIES': 2000,
            },
        }
    }

DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760

LATE_API_KEY = config('Late', default='')

LINKEDIN_CLIENT_ID = config('LINKEDIN_CLIENT_ID', default='')
LINKEDIN_CLIENT_SECRET = config('LINKEDIN_CLIENT_SECRET', default='')
LINKEDIN_ORG_ID = config('LINKEDIN_ORG_ID', default='')
LINKEDIN_REDIRECT_URI = config('LINKEDIN_REDIRECT_URI', default='http://127.0.0.1:8000/social-analytics/linkedin/callback/')

FACEBOOK_APP_ID = config('FACEBOOK_APP_ID', default='')
FACEBOOK_APP_SECRET = config('FACEBOOK_APP_SECRET', default='')

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = 'login'
