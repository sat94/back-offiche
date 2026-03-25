import json
import os
import time
from datetime import datetime, timezone
from urllib.parse import urlencode

import requests
from django.conf import settings

LINKEDIN_API_BASE = 'https://api.linkedin.com/v2'
LINKEDIN_AUTH_URL = 'https://www.linkedin.com/oauth/v2/authorization'
LINKEDIN_TOKEN_URL = 'https://www.linkedin.com/oauth/v2/accessToken'

SCOPES = [
    'openid',
    'profile',
    'email',
    'w_member_social',
]

TOKEN_FILE = os.path.join(settings.BASE_DIR, 'linkedin_token.json')


def _load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_token(token_data):
    token_data['saved_at'] = int(time.time())
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f)


def get_access_token():
    return _load_token().get('access_token', '')


def is_token_valid():
    token_data = _load_token()
    if not token_data.get('access_token'):
        return False
    saved_at = token_data.get('saved_at', 0)
    expires_in = token_data.get('expires_in', 5183999)
    return int(time.time()) < saved_at + expires_in - 300


def get_auth_url(redirect_uri, state='linkedin_oauth'):
    params = {
        'response_type': 'code',
        'client_id': settings.LINKEDIN_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'scope': ' '.join(SCOPES),
        'state': state,
    }
    return f"{LINKEDIN_AUTH_URL}?{urlencode(params)}"


def exchange_code_for_token(code, redirect_uri):
    r = requests.post(LINKEDIN_TOKEN_URL, data={
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': settings.LINKEDIN_CLIENT_ID,
        'client_secret': settings.LINKEDIN_CLIENT_SECRET,
    }, timeout=15)
    r.raise_for_status()
    return r.json()


def _headers():
    return {
        'Authorization': f'Bearer {get_access_token()}',
        'X-Restli-Protocol-Version': '2.0.0',
    }


def _ts_to_iso(ts_ms):
    if not ts_ms:
        return None
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).isoformat()


def _get_person_urn():
    token_data = _load_token()
    if token_data.get('person_urn'):
        return token_data['person_urn']
    r = requests.get(
        f'{LINKEDIN_API_BASE}/userinfo',
        headers=_headers(),
        timeout=10,
    )
    r.raise_for_status()
    sub = r.json().get('sub', '')
    person_urn = f'urn:li:person:{sub}'
    token_data['person_urn'] = person_urn
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f)
    return person_urn


def fetch_posts(page=1, limit=20, from_date=None, to_date=None):
    person_urn = _get_person_urn()
    start = (page - 1) * limit

    r = requests.get(
        f'{LINKEDIN_API_BASE}/ugcPosts',
        headers=_headers(),
        params={
            'q': 'authors',
            'authors': f'List({person_urn})',
            'count': limit,
            'start': start,
        },
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()
    posts = data.get('elements', [])
    total = data.get('paging', {}).get('total', 0)

    if not posts:
        return {'posts': [], 'overview': {'totalPosts': total}}

    post_urns = [p['id'] for p in posts]
    stats_map = _fetch_post_statistics(post_urns)

    result = []
    for post in posts:
        post_id = post.get('id', '')
        stats = stats_map.get(post_id, {})

        content_data = (
            post.get('specificContent', {})
            .get('com.linkedin.ugc.ShareContent', {})
        )
        text = content_data.get('shareCommentary', {}).get('text', '')
        media = content_data.get('media', [])
        thumbnail = None
        if media:
            thumbs = media[0].get('thumbnails', [])
            if thumbs:
                thumbnail = thumbs[0].get('url')

        published_at = _ts_to_iso(post.get('firstPublishedAt'))

        likes = stats.get('numLikes', 0)
        comments = stats.get('numComments', 0)
        shares = stats.get('numShares', 0)
        total_engagement = likes + comments + shares
        engagement_rate = round(total_engagement / 100, 2) if total_engagement > 0 else 0

        result.append({
            'id': post_id,
            'content': text,
            'thumbnailUrl': thumbnail,
            'platformPostUrl': f'https://www.linkedin.com/feed/update/{post_id}/',
            'publishedAt': published_at,
            'platforms': [{'platform': 'linkedin', 'accountUsername': 'Serge Doorgachurn'}],
            'analytics': {
                'impressions': 0,
                'reach': 0,
                'likes': likes,
                'comments': comments,
                'shares': shares,
                'clicks': 0,
                'saves': 0,
                'engagementRate': engagement_rate,
            },
        })

    return {
        'posts': result,
        'overview': {'totalPosts': total},
    }


def _fetch_post_statistics(post_urns):
    stats_map = {}
    try:
        encoded_urns = [f'urn%3Ali%3AugcPost%3A{u.split(":")[-1]}' for u in post_urns]
        r = requests.get(
            f'{LINKEDIN_API_BASE}/socialActions',
            headers=_headers(),
            params={'ids': f"List({','.join(encoded_urns)})"},
            timeout=15,
        )
        if r.ok:
            for urn, val in r.json().get('results', {}).items():
                stats_map[urn] = val
    except Exception:
        pass

    if not stats_map:
        for urn in post_urns:
            try:
                r = requests.get(
                    f'{LINKEDIN_API_BASE}/socialActions/{requests.utils.quote(urn, safe="")}',
                    headers=_headers(),
                    timeout=10,
                )
                if r.ok:
                    stats_map[urn] = r.json()
            except Exception:
                pass

    return stats_map
