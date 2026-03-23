import threading
import time
import uuid
import urllib.request
import urllib.parse
import json
from decouple import config

TOKEN_URL = 'https://auth.contabo.com/auth/realms/contabo/protocol/openid-connect/token'
API_BASE = 'https://api.contabo.com/v1'

_token_cache = {'access_token': None, 'expires_at': 0}
_token_lock = threading.Lock()


def _get_token():
    with _token_lock:
        if _token_cache['access_token'] and time.time() < _token_cache['expires_at'] - 30:
            return _token_cache['access_token']

        data = urllib.parse.urlencode({
            'grant_type': 'password',
            'client_id': config('CONTABO_CLIENT_ID'),
            'client_secret': config('CONTABO_CLIENT_SECRET'),
            'username': config('CONTABO_USERNAME'),
            'password': config('CONTABO_PASSWORD'),
        }).encode()

        req = urllib.request.Request(TOKEN_URL, data=data, headers={
            'Content-Type': 'application/x-www-form-urlencoded',
        })
        resp = urllib.request.urlopen(req, timeout=15)
        body = json.loads(resp.read())

        _token_cache['access_token'] = body['access_token']
        _token_cache['expires_at'] = time.time() + body.get('expires_in', 300)
        return _token_cache['access_token']


def _api_request(method, path, body=None):
    token = _get_token()
    url = f'{API_BASE}{path}'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'x-request-id': str(uuid.uuid4()),
    }
    if body is not None:
        req_data = json.dumps(body).encode()
    elif method in ('POST', 'PUT', 'PATCH'):
        req_data = b'{}'
    else:
        req_data = None
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    resp = urllib.request.urlopen(req, timeout=30)
    if resp.status == 204:
        return {}
    return json.loads(resp.read())


def list_instances():
    result = _api_request('GET', '/compute/instances?size=100')
    return result.get('data', [])


def instance_action(instance_id, action):
    return _api_request('POST', f'/compute/instances/{instance_id}/actions/{action}')


def list_snapshots(instance_id):
    result = _api_request('GET', f'/compute/instances/{instance_id}/snapshots?size=100')
    return result.get('data', [])


def change_password(instance_id, new_password):
    return _api_request('PATCH', f'/compute/instances/{instance_id}', {
        'rootPassword': new_password,
    })


def reinstall_os(instance_id, image_id):
    return _api_request('PUT', f'/compute/instances/{instance_id}', {
        'imageId': image_id,
    })


def list_images():
    result = _api_request('GET', '/compute/images?size=100&type=standard')
    return result.get('data', [])
