import threading
import time
import paramiko

SSH_KEY_PATH = 'C:/Users/sulta/.ssh/id_ed25519'

_sessions = {}
_sessions_lock = threading.Lock()


SERVERS = [
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
    ('pg_vectorielle', 'PostgreSQL Vectorielle', '144.91.110.197', 'root'),
]


def get_server_list():
    return [{'key': k, 'label': l, 'host': h, 'user': u} for k, l, h, u in SERVERS]


def connect(session_id, server_key, password=None):
    srv = None
    for k, l, h, u in SERVERS:
        if k == server_key:
            srv = (k, l, h, u)
            break
    if not srv:
        raise ValueError(f'Serveur inconnu: {server_key}')

    key, label, host, user = srv

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(host, username=user, key_filename=SSH_KEY_PATH, timeout=15)
    except Exception:
        if password:
            client.connect(host, username=user, password=password, timeout=15)
        else:
            raise

    channel = client.invoke_shell(term='xterm', width=120, height=40)
    channel.settimeout(0.1)

    with _sessions_lock:
        old = _sessions.pop(session_id, None)
        if old:
            try:
                old['channel'].close()
                old['client'].close()
            except Exception:
                pass

        _sessions[session_id] = {
            'client': client,
            'channel': channel,
            'server_key': server_key,
            'host': host,
            'user': user,
            'label': label,
            'connected_at': time.time(),
        }

    return {'ok': True, 'server': label, 'host': host, 'user': user}


def execute(session_id, command):
    with _sessions_lock:
        sess = _sessions.get(session_id)
    if not sess:
        return {'error': 'Session non connectée'}

    channel = sess['channel']
    try:
        channel.send(command + '\n')
        time.sleep(0.5)

        output = ''
        deadline = time.time() + 5
        while time.time() < deadline:
            try:
                chunk = channel.recv(65536)
                if chunk:
                    output += chunk.decode('utf-8', errors='replace')
                    if channel.recv_ready():
                        continue
                    time.sleep(0.2)
                    if not channel.recv_ready():
                        break
                else:
                    break
            except Exception:
                break

        return {'output': output}
    except Exception as e:
        return {'error': str(e)}


def read_output(session_id):
    with _sessions_lock:
        sess = _sessions.get(session_id)
    if not sess:
        return {'error': 'Session non connectée'}

    channel = sess['channel']
    output = ''
    try:
        while channel.recv_ready():
            chunk = channel.recv(65536)
            if chunk:
                output += chunk.decode('utf-8', errors='replace')
    except Exception:
        pass
    return {'output': output}


def disconnect(session_id):
    with _sessions_lock:
        sess = _sessions.pop(session_id, None)
    if sess:
        try:
            sess['channel'].close()
            sess['client'].close()
        except Exception:
            pass
    return {'ok': True}


def get_session_info(session_id):
    with _sessions_lock:
        sess = _sessions.get(session_id)
    if not sess:
        return None
    return {
        'server_key': sess['server_key'],
        'label': sess['label'],
        'host': sess['host'],
        'user': sess['user'],
    }


def cleanup_stale(max_age=1800):
    now = time.time()
    with _sessions_lock:
        stale = [sid for sid, s in _sessions.items() if now - s['connected_at'] > max_age]
        for sid in stale:
            sess = _sessions.pop(sid)
            try:
                sess['channel'].close()
                sess['client'].close()
            except Exception:
                pass
