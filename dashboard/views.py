import json
import subprocess
import sys
import time
import requests as http_requests
from datetime import datetime, timedelta
from functools import wraps
from dateutil import parser as dateutil_parser


def _parse_date(val):
    if not val or not isinstance(val, str):
        return val
    try:
        return dateutil_parser.parse(val)
    except Exception:
        return val

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import connections
from django.db.models import Count, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages as django_messages
from django.utils import timezone

from core.models import UserEvent
from compte.models import (
    Compte, Photo, PhotoComment, ProfileComment, VideoComment,
    CompteLike, CompteProfileVue, CompteBlacklist,
    SignalementUtilisateur,
    CompteAttranceGenre, CompteCaractere, CompteHobie,
    CompteLangue, ComptePreferenceEthnique, CompteTendance,
    CompteFilm, CompteMusique, CompteSortie, CompteZonesConfort,
)
from content.models import PgArticle, ArticleView
from core.models import PlanAbonnement, Facture as PgFacture
from back_office.mongodb import get_mongo_database, get_all_mongo_connections
from dashboard.contabo import list_instances, instance_action, list_snapshots, change_password, reinstall_os, list_images


def _safe_count(model):
    try:
        return model.objects.count()
    except Exception:
        return 0


def _cached(key, timeout=60):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = cache.get(key)
            if result is None:
                result = func(*args, **kwargs)
                cache.set(key, result, timeout)
            return result
        return wrapper
    return decorator


@login_required
def index(request):
    cached = cache.get('dashboard_index')
    if cached:
        return render(request, 'dashboard/index.html', cached)

    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)

    try:
        stats = Compte.objects.aggregate(
            total=Count('id'),
            new_30d=Count('id', filter=Q(created_at__gte=thirty_days_ago)),
            new_7d=Count('id', filter=Q(created_at__gte=seven_days_ago)),
            verified=Count('id', filter=Q(is_verified=True)),
            inactive=Count('id', filter=Q(is_active=False)),
        )
        total_comptes = stats['total']
        new_comptes_30d = stats['new_30d']
        new_comptes_7d = stats['new_7d']
        verified_comptes = stats['verified']
        inactive_comptes = stats['inactive']
    except Exception:
        total_comptes = new_comptes_30d = new_comptes_7d = verified_comptes = inactive_comptes = 0

    deleted_comptes = 0
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute("SELECT total FROM compte_supprime LIMIT 1")
            row = cursor.fetchone()
            if row:
                deleted_comptes = row[0]
    except Exception:
        pass

    chart_labels, chart_data = [], []
    try:
        comptes_par_jour = list(
            Compte.objects.filter(created_at__gte=thirty_days_ago)
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )
        chart_labels = [c['date'].strftime('%d/%m') for c in comptes_par_jour]
        chart_data = [c['count'] for c in comptes_par_jour]
    except Exception:
        pass

    try:
        with connections['default'].cursor() as cursor:
            cursor.execute("""
                SELECT
                    (SELECT COUNT(*) FROM compte_like) AS likes,
                    (SELECT COUNT(*) FROM compte_profile_vue) AS vues,
                    (SELECT COUNT(*) FROM compte_photo) AS photos,
                    (SELECT COUNT(*) FROM compte_blacklist) AS blacklist,
                    (SELECT COUNT(*) FROM compte_signalement_utilisateur) AS signalements
            """)
            row = cursor.fetchone()
            total_likes, total_vues, total_photos, total_blacklist, total_signalements = row
    except Exception:
        total_likes = _safe_count(CompteLike)
        total_vues = _safe_count(CompteProfileVue)
        total_photos = _safe_count(Photo)
        total_blacklist = _safe_count(CompteBlacklist)
        total_signalements = _safe_count(SignalementUtilisateur)

    mongo_status = cache.get('mongo_status')
    if mongo_status is None:
        try:
            mongo_status = get_all_mongo_connections()
            cache.set('mongo_status', mongo_status, 120)
        except Exception:
            mongo_status = {}

    pg_ok = True

    context = {
        'total_comptes': total_comptes,
        'new_comptes_30d': new_comptes_30d,
        'new_comptes_7d': new_comptes_7d,
        'verified_comptes': verified_comptes,
        'inactive_comptes': inactive_comptes,
        'deleted_comptes': deleted_comptes,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'total_likes': total_likes,
        'total_vues': total_vues,
        'total_photos': total_photos,
        'total_blacklist': total_blacklist,
        'total_signalements': total_signalements,
        'mongo_status': mongo_status,
        'pg_ok': pg_ok,
    }
    cache.set('dashboard_index', context, 30)
    return render(request, 'dashboard/index.html', context)


@login_required
def comptes_list(request):
    search = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    sort = request.GET.get('sort', '-created_at')

    qs = Compte.objects.only(
        'id', 'username', 'email', 'prenom', 'nom', 'ville',
        'abonnement', 'is_verified', 'is_active', 'is_online', 'created_at',
    ).exclude(email__endswith='@meet-voice-test.fr')
    if search:
        qs = qs.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(prenom__icontains=search) |
            Q(nom__icontains=search)
        )
    if status_filter == 'verified':
        qs = qs.filter(is_verified=True)
    elif status_filter == 'unverified':
        qs = qs.filter(is_verified=False)
    elif status_filter == 'online':
        qs = qs.filter(is_online=True)
    elif status_filter == 'inactive':
        qs = qs.filter(is_active=False)

    qs = qs.order_by(sort)

    chart_cache_key = 'comptes_chart_data'
    chart_cached = cache.get(chart_cache_key)
    if chart_cached:
        chart_labels, chart_data = chart_cached
    else:
        chart_labels, chart_data = [], []
        try:
            comptes_par_mois = list(
                Compte.objects.annotate(mois=TruncMonth('created_at'))
                .values('mois')
                .annotate(count=Count('id'))
                .order_by('mois')
            )
            chart_labels = [c['mois'].strftime('%m/%Y') if c['mois'] else '' for c in comptes_par_mois]
            chart_data = [c['count'] for c in comptes_par_mois]
            cache.set(chart_cache_key, (chart_labels, chart_data), 300)
        except Exception:
            pass

    comptes = list(qs[:200])
    total = len(comptes) if len(comptes) < 200 else qs.count()

    context = {
        'comptes': comptes,
        'search': search,
        'status_filter': status_filter,
        'sort': sort,
        'total': total,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
    }
    return render(request, 'dashboard/comptes.html', context)


def _safe_m2m(model, compte, value_field):
    try:
        return list(model.objects.filter(compte=compte).select_related().values_list(value_field, flat=True))
    except Exception:
        return []


@login_required
def compte_detail(request, pk):
    compte = get_object_or_404(Compte, pk=pk)
    photos = Photo.objects.only(
        'id', 'photos', 'type_photo', 'ordre', 'est_active', 'is_nsfw', 'is_shocking', 'thumbnail',
    ).filter(compte=compte).order_by('ordre')

    try:
        with connections['default'].cursor() as cursor:
            cursor.execute("""
                SELECT
                    (SELECT COUNT(*) FROM compte_like WHERE compte_id = %s),
                    (SELECT COUNT(*) FROM compte_like WHERE like_id = %s),
                    (SELECT COUNT(*) FROM compte_profile_vue WHERE viewed_id = %s),
                    (SELECT COUNT(*) FROM compte_blacklist WHERE bloque_id = %s),
                    (SELECT COUNT(*) FROM compte_signalement_utilisateur WHERE signale_id = %s)
            """, [str(pk), str(pk), str(pk), str(pk), str(pk)])
            row = cursor.fetchone()
            likes_given, likes_received, views_received, blacklisted_by, signalements = row
    except Exception:
        likes_given = CompteLike.objects.filter(compte=compte).count()
        likes_received = CompteLike.objects.filter(like=compte).count()
        views_received = CompteProfileVue.objects.filter(viewed=compte).count()
        blacklisted_by = CompteBlacklist.objects.filter(bloque=compte).count()
        signalements = SignalementUtilisateur.objects.filter(signale=compte).count()

    m2m_data = [
        {'label': 'Attirance genre', 'icon': 'bi-gender-ambiguous', 'color': '#e84393', 'items': _safe_m2m(CompteAttranceGenre, compte, 'genre')},
        {'label': 'Caractères', 'icon': 'bi-emoji-smile', 'color': '#6c5ce7', 'items': _safe_m2m(CompteCaractere, compte, 'caractere__caractere')},
        {'label': 'Hobbies', 'icon': 'bi-controller', 'color': '#00cec9', 'items': _safe_m2m(CompteHobie, compte, 'hobie__hobie')},
        {'label': 'Langues', 'icon': 'bi-translate', 'color': '#0984e3', 'items': _safe_m2m(CompteLangue, compte, 'langue__langue')},
        {'label': 'Préf. ethniques', 'icon': 'bi-globe2', 'color': '#fdcb6e', 'items': _safe_m2m(ComptePreferenceEthnique, compte, 'preferenceethnique__nom')},
        {'label': 'Tendances', 'icon': 'bi-fire', 'color': '#e17055', 'items': _safe_m2m(CompteTendance, compte, 'tendance__tendance')},
        {'label': 'Films', 'icon': 'bi-film', 'color': '#a29bfe', 'items': _safe_m2m(CompteFilm, compte, 'film__film')},
        {'label': 'Musique', 'icon': 'bi-music-note-beamed', 'color': '#55efc4', 'items': _safe_m2m(CompteMusique, compte, 'musique__musique')},
        {'label': 'Sorties', 'icon': 'bi-cup-straw', 'color': '#fab1a0', 'items': _safe_m2m(CompteSortie, compte, 'preference')},
        {'label': 'Zones de confort', 'icon': 'bi-shield-check', 'color': '#74b9ff', 'items': _safe_m2m(CompteZonesConfort, compte, 'zone')},
    ]

    context = {
        'compte': compte,
        'photos': photos,
        'likes_given': likes_given,
        'likes_received': likes_received,
        'views_received': views_received,
        'blacklisted_by': blacklisted_by,
        'signalements': signalements,
        'm2m_data': m2m_data,
    }
    return render(request, 'dashboard/compte_detail.html', context)


@login_required
@require_POST
def compte_toggle(request, pk, field):
    allowed = ['is_verified', 'is_active', 'is_online', 'is_admin', 'is_staff', 'ghost']
    if field not in allowed:
        return JsonResponse({'error': 'Field not allowed'}, status=400)

    compte = get_object_or_404(Compte, pk=pk)
    current = getattr(compte, field)
    setattr(compte, field, not current)
    compte.save(update_fields=[field])
    return JsonResponse({'ok': True, 'field': field, 'value': not current})


@login_required
@require_POST
def compte_delete(request, pk):
    compte = get_object_or_404(Compte, pk=pk)
    username = compte.username
    compte.delete()
    django_messages.success(request, f"Compte '{username}' supprime.")
    return redirect('dashboard:comptes')


@login_required
def moderation(request):
    nsfw_photos = Photo.objects.only(
        'id', 'compte_id', 'photos', 'type_photo', 'date_ajout', 'is_nsfw', 'is_shocking',
    ).filter(is_nsfw=True).order_by('-date_ajout')[:50]
    shocking_photos = Photo.objects.only(
        'id', 'compte_id', 'photos', 'type_photo', 'date_ajout', 'is_nsfw', 'is_shocking',
    ).filter(is_shocking=True).order_by('-date_ajout')[:50]
    profile_comments = ProfileComment.objects.select_related('auteur', 'profil_utilisateur').only(
        'id', 'contenu', 'date_creation', 'auteur__username', 'profil_utilisateur__username',
    ).order_by('-date_creation')[:100]
    photo_comments = PhotoComment.objects.select_related('auteur', 'photo').only(
        'id', 'contenu', 'date_creation', 'auteur__username', 'photo__id',
    ).order_by('-date_creation')[:100]
    try:
        video_comments = VideoComment.objects.select_related('auteur', 'video').only(
            'id', 'contenu', 'date_creation', 'auteur__username', 'video__id',
        ).order_by('-date_creation')[:100]
    except Exception:
        video_comments = []
    blacklist = CompteBlacklist.objects.select_related('bloqueur', 'bloque').only(
        'id', 'date_creation', 'bloqueur__username', 'bloque__username',
    ).order_by('-date_creation')[:50]
    signalements = SignalementUtilisateur.objects.select_related('signaleur', 'signale').only(
        'id', 'motif', 'description', 'date_creation', 'statut',
        'signaleur__username', 'signale__username',
    ).order_by('-date_creation')[:50]

    mongo_posts = []
    total_comments = 0
    total_replies = 0
    try:
        db = get_mongo_database('api')
        for post in db['posts'].find({}, {
            'date_creation': 1, 'content': 1, 'author': 1, 'comments': 1, 'user_id': 1,
        }).sort('_id', -1).limit(50):
            post['id'] = str(post['_id'])
            del post['_id']
            post['date_creation'] = _parse_date(post.get('date_creation'))
            comments = post.get('comments', [])
            for c in comments:
                c['date_creation'] = _parse_date(c.get('date_creation'))
                total_comments += 1
                for r in c.get('replies', []):
                    r['date_creation'] = _parse_date(r.get('date_creation'))
                    total_replies += 1
            mongo_posts.append(post)
    except Exception:
        pass

    event_comments = []
    events_list = []
    event_map = {}
    event_comments_grouped = {}
    try:
        ev_db = get_mongo_database('event')
        for ev in ev_db['events'].find({}, {'title': 1, 'event_type': 1, 'lieu': 1, 'image_url': 1}):
            eid = str(ev['_id'])
            title = ev.get('title', 'Sans titre')
            event_map[eid] = title
            events_list.append({
                'id': eid,
                'title': title,
                'event_type': ev.get('event_type', ''),
                'lieu': ev.get('lieu', ''),
                'image_url': ev.get('image_url', ''),
            })
        for c in ev_db['comments'].find().sort('_id', -1).limit(200):
            c['id'] = str(c['_id'])
            del c['_id']
            eid = c.get('event_id', '')
            c['event_title'] = event_map.get(eid, 'Inconnu')
            c['created_at'] = c.get('created_at')
            event_comments.append(c)
            event_comments_grouped.setdefault(eid, []).append(c)
    except Exception:
        pass

    mongo_messages = []
    try:
        gw_db = get_mongo_database('gateway')
        for msg in gw_db['messages'].find({}, {
            'from': 1, 'to': 1, 'content': 1, 'timestamp': 1, 'type': 1,
        }).sort('_id', -1).limit(200):
            msg['id'] = str(msg.pop('_id'))
            msg['timestamp'] = _parse_date(msg.get('timestamp'))
            mongo_messages.append(msg)
    except Exception:
        pass

    conversations = {}
    for msg in mongo_messages:
        pair = tuple(sorted([msg.get('from', ''), msg.get('to', '')]))
        conversations.setdefault(pair, []).append(msg)

    context = {
        'nsfw_photos': nsfw_photos,
        'shocking_photos': shocking_photos,
        'profile_comments': profile_comments,
        'photo_comments': photo_comments,
        'video_comments': video_comments,
        'blacklist': blacklist,
        'signalements': signalements,
        'mongo_posts': mongo_posts,
        'total_mongo_posts': len(mongo_posts),
        'total_mongo_comments': total_comments,
        'total_mongo_replies': total_replies,
        'mongo_messages': mongo_messages,
        'conversations': conversations,
        'event_comments': event_comments,
        'events_list': events_list,
        'event_comments_grouped': event_comments_grouped,
    }
    return render(request, 'dashboard/moderation.html', context)


@login_required
@require_POST
def photo_moderate(request, pk):
    photo = get_object_or_404(Photo, pk=pk)
    action = request.POST.get('action')
    if action == 'approve':
        photo.is_nsfw = False
        photo.is_shocking = False
        photo.is_nsfw_checked = True
        photo.is_shocking_checked = True
        photo.save(update_fields=['is_nsfw', 'is_shocking', 'is_nsfw_checked', 'is_shocking_checked'])
    elif action == 'reject':
        photo.est_active = False
        photo.save(update_fields=['est_active'])
    return JsonResponse({'ok': True})


@login_required
@require_POST
def mongo_post_delete(request, post_id):
    try:
        from bson import ObjectId
        db = get_mongo_database('api')
        db['posts'].delete_one({'_id': ObjectId(post_id)})
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def mongo_comment_delete(request, post_id, comment_id):
    try:
        from bson import ObjectId
        db = get_mongo_database('api')
        db['posts'].update_one(
            {'_id': ObjectId(post_id)},
            {'$pull': {'comments': {'id': comment_id}}}
        )
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def mongo_reply_delete(request, post_id, comment_id, reply_id):
    try:
        from bson import ObjectId
        db = get_mongo_database('api')
        db['posts'].update_one(
            {'_id': ObjectId(post_id), 'comments.id': comment_id},
            {'$pull': {'comments.$.replies': {'id': reply_id}}}
        )
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def mongo_message_delete(request, msg_id):
    try:
        from bson import ObjectId
        db = get_mongo_database('gateway')
        db['messages'].delete_one({'_id': ObjectId(msg_id)})
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def event_comment_delete(request, comment_id):
    try:
        from bson import ObjectId
        db = get_mongo_database('event')
        db['comments'].delete_one({'_id': ObjectId(comment_id)})
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def event_comment_toggle_hide(request, comment_id):
    try:
        from bson import ObjectId
        db = get_mongo_database('event')
        comment = db['comments'].find_one({'_id': ObjectId(comment_id)})
        if not comment:
            return JsonResponse({'error': 'Commentaire non trouvé'}, status=404)
        new_val = not comment.get('is_hidden', False)
        db['comments'].update_one(
            {'_id': ObjectId(comment_id)},
            {'$set': {'is_hidden': new_val}}
        )
        return JsonResponse({'ok': True, 'is_hidden': new_val})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def event_comment_edit(request, comment_id):
    try:
        import json as _json
        from bson import ObjectId
        body = _json.loads(request.body)
        message = body.get('message', '')
        if not message:
            return JsonResponse({'error': 'Message requis'}, status=400)
        db = get_mongo_database('event')
        db['comments'].update_one(
            {'_id': ObjectId(comment_id)},
            {'$set': {'message': message}}
        )
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def databases(request):
    cached = cache.get('databases_view')
    if cached:
        return render(request, 'dashboard/databases.html', cached)

    pg_info = {}
    try:
        conn = connections['default']
        conn.ensure_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT s.relname AS table_name,
                       s.n_live_tup AS row_estimate
                FROM pg_stat_user_tables s
                ORDER BY s.relname
            """)
            table_details = [{'name': row[0], 'count': row[1]} for row in cursor.fetchall()]

            pg_info = {
                'status': 'connected',
                'tables': table_details,
                'total_tables': len(table_details),
            }
    except Exception as e:
        pg_info = {'status': 'error', 'error': str(e)}

    mongo_info = {}
    try:
        mongo_info = get_all_mongo_connections()
        for key, info in mongo_info.items():
            if info.get('status') == 'connected':
                db = get_mongo_database(key)
                collections_detail = []
                for cname in info.get('collections', []):
                    try:
                        count = db[cname].estimated_document_count()
                    except Exception:
                        count = '?'
                    collections_detail.append({'name': cname, 'count': count})
                info['collections_detail'] = collections_detail
    except Exception as e:
        mongo_info = {'_error': str(e)}

    context = {
        'pg_info': pg_info,
        'mongo_info': mongo_info,
    }
    cache.set('databases_view', context, 60)
    return render(request, 'dashboard/databases.html', context)


@login_required
def mongo_collection_view(request, db_key, collection_name):
    try:
        db = get_mongo_database(db_key)
        collection = db[collection_name]
        page = int(request.GET.get('page', 1))
        per_page = 20
        skip = (page - 1) * per_page
        total = collection.estimated_document_count()
        docs = list(collection.find().sort('_id', -1).skip(skip).limit(per_page))

        for doc in docs:
            doc['_id'] = str(doc['_id'])
            for k, v in doc.items():
                if isinstance(v, datetime):
                    doc[k] = v.strftime('%d/%m/%Y %H:%M')
                elif hasattr(v, '__str__') and not isinstance(v, (str, int, float, bool, list, dict)):
                    doc[k] = str(v)

        context = {
            'db_key': db_key,
            'collection_name': collection_name,
            'documents': docs,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
        }
        return render(request, 'dashboard/mongo_collection.html', context)
    except Exception as e:
        django_messages.error(request, f"Erreur: {e}")
        return redirect('dashboard:databases')


@login_required
@require_POST
def mongo_doc_delete(request, db_key, collection_name, doc_id):
    try:
        from bson import ObjectId
        db = get_mongo_database(db_key)
        db[collection_name].delete_one({'_id': ObjectId(doc_id)})
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def pg_table_view(request, table_name):
    try:
        conn = connections['default']
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = %s AND table_schema = 'public'
                ORDER BY ordinal_position
            """, [table_name])
            columns = [{'name': row[0], 'type': row[1]} for row in cursor.fetchall()]
            col_names = [c['name'] for c in columns]

            page = int(request.GET.get('page', 1))
            per_page = 20
            offset = (page - 1) * per_page

            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            total = cursor.fetchone()[0]

            cursor.execute(f'SELECT * FROM "{table_name}" LIMIT %s OFFSET %s', [per_page, offset])
            rows = cursor.fetchall()

        context = {
            'table_name': table_name,
            'columns': columns,
            'col_names': col_names,
            'rows': rows,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
        }
        return render(request, 'dashboard/pg_table.html', context)
    except Exception as e:
        django_messages.error(request, f"Erreur: {e}")
        return redirect('dashboard:databases')


@login_required
def run_tests(request):
    return render(request, 'dashboard/tests.html')


@login_required
def run_tests_api(request):
    import os
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        result = subprocess.run(
            [sys.executable, 'manage.py', 'test', 'dashboard', '-v', '2', '--no-input'],
            capture_output=True, text=True, timeout=120,
            cwd=project_dir,
        )
    except Exception as e:
        return JsonResponse({'output': str(e), 'returncode': 1})

    return JsonResponse({
        'output': result.stdout + result.stderr,
        'returncode': result.returncode,
    })


@login_required
def plans_list(request):
    from dashboard.mollie_helper import get_stats, list_payments, list_customers, list_all_subscriptions, list_refunds
    tab = request.GET.get('tab', 'overview')
    stats = {}
    payments = []
    customers = []
    subscriptions = []
    refunds = []
    error = None
    try:
        stats = cache.get('mollie_stats')
        if stats is None:
            stats = get_stats()
            cache.set('mollie_stats', stats, 120)
        if tab in ('payments', 'overview'):
            payments = list_payments()
        if tab in ('customers', 'overview'):
            customers = list_customers()
        if tab in ('subscriptions', 'overview'):
            subscriptions = list_all_subscriptions()
        if tab == 'refunds':
            refunds = list_refunds()
    except Exception as e:
        error = str(e)
    context = {
        'tab': tab,
        'stats': stats,
        'payments': payments,
        'customers': customers,
        'subscriptions': subscriptions,
        'refunds': refunds,
        'error': error,
    }
    return render(request, 'dashboard/plans.html', context)


@login_required
def mollie_customer_detail(request, customer_id):
    from dashboard.mollie_helper import get_customer_detail
    try:
        data = get_customer_detail(customer_id)
    except Exception as e:
        data = {'error': str(e)}
    return JsonResponse(data)


@login_required
@require_POST
def mollie_cancel_subscription(request):
    from dashboard.mollie_helper import cancel_subscription
    customer_id = request.POST.get('customer_id')
    subscription_id = request.POST.get('subscription_id')
    try:
        cancel_subscription(customer_id, subscription_id)
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def mollie_refund(request):
    from dashboard.mollie_helper import create_refund
    payment_id = request.POST.get('payment_id')
    try:
        create_refund(payment_id)
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def factures_list(request):
    factures = PgFacture.objects.select_related('user').all().order_by('-date_emission')[:200]
    context = {'factures': factures}
    return render(request, 'dashboard/factures.html', context)


@login_required
def monitoring(request):
    from django.conf import settings as s
    context = {
        'targets': s.MONITORING_TARGETS,
        'targets_json': json.dumps({k: v['label'] for k, v in s.MONITORING_TARGETS.items()}),
    }
    return render(request, 'dashboard/monitoring.html', context)


_prev_net = {}
_prev_cpu = {}


def _parse_metrics(text):
    result = {}
    for line in text.strip().split('\n'):
        if line.startswith('#'):
            continue
        parts = line.split()
        if len(parts) >= 2:
            key = parts[0]
            try:
                val = float(parts[1])
            except ValueError:
                continue
            if key in result:
                if not isinstance(result[key], list):
                    result[key] = [result[key]]
                result[key].append(val)
            else:
                result[key] = val
    return result


def _get_metric(metrics, prefix, labels=None):
    if labels:
        search = f'{prefix}{{{labels}}}'
        for line_key, val in metrics.items():
            if line_key.startswith(prefix) and all(l in line_key for l in labels.split(',')):
                return val
    return metrics.get(prefix)


def _fetch_single_metric(key, port):
    import urllib.request
    try:
        url = f'http://127.0.0.1:{port}/metrics'
        req = urllib.request.urlopen(url, timeout=5)
        return key, req.read().decode('utf-8', errors='replace'), None
    except Exception as e:
        return key, None, str(e)


@login_required
def monitoring_api(request):
    from concurrent.futures import ThreadPoolExecutor
    from django.conf import settings as s

    results = {}

    with ThreadPoolExecutor(max_workers=min(8, len(s.MONITORING_TARGETS))) as executor:
        futures = {
            executor.submit(_fetch_single_metric, key, info['local_port']): key
            for key, info in s.MONITORING_TARGETS.items()
        }

    fetched = {}
    for future in futures:
        key, raw, error = future.result()
        if error:
            results[key] = {'error': error}
        else:
            fetched[key] = raw

    for key, raw in fetched.items():
        try:

            m = {}
            cpu_idle_total = 0.0
            cpu_total = 0.0
            cpu_count = 0
            net_rx = 0.0
            net_tx = 0.0
            disk_size = 0.0
            disk_avail = 0.0

            seen_cpus = set()

            for line in raw.split('\n'):
                if line.startswith('#') or not line.strip():
                    continue
                parts = line.rsplit(' ', 1)
                if len(parts) < 2:
                    continue
                metric_part = parts[0]
                try:
                    val = float(parts[1])
                except ValueError:
                    continue

                if metric_part.startswith('node_cpu_seconds_total{'):
                    if 'cpu="' in metric_part:
                        cpu_id = metric_part.split('cpu="')[1].split('"')[0]
                        seen_cpus.add(cpu_id)
                    cpu_total += val
                    if 'mode="idle"' in metric_part:
                        cpu_idle_total += val

                elif metric_part == 'node_memory_MemTotal_bytes':
                    m['mem_total'] = val
                elif metric_part == 'node_memory_MemAvailable_bytes':
                    m['mem_available'] = val

                elif 'mountpoint="/"' in metric_part and 'fstype="rootfs"' not in metric_part:
                    if metric_part.startswith('node_filesystem_size_bytes{'):
                        disk_size = val
                    elif metric_part.startswith('node_filesystem_avail_bytes{'):
                        disk_avail = val

                elif metric_part.startswith('node_network_receive_bytes_total{'):
                    if 'device="lo"' not in metric_part and 'device="veth' not in metric_part and 'device="docker' not in metric_part and 'device="br-' not in metric_part:
                        net_rx += val
                elif metric_part.startswith('node_network_transmit_bytes_total{'):
                    if 'device="lo"' not in metric_part and 'device="veth' not in metric_part and 'device="docker' not in metric_part and 'device="br-' not in metric_part:
                        net_tx += val

                elif metric_part == 'node_load1':
                    m['load1'] = val
                elif metric_part == 'node_load5':
                    m['load5'] = val
                elif metric_part == 'node_load15':
                    m['load15'] = val
                elif metric_part == 'node_boot_time_seconds':
                    m['boot_time'] = val

            cpu_count = len(seen_cpus) if seen_cpus else 1

            now = time.time()
            prev = _prev_cpu.get(key)
            if prev:
                dt = now - prev['time']
                if dt > 0:
                    idle_diff = cpu_idle_total - prev['idle']
                    total_diff = cpu_total - prev['total']
                    if total_diff > 0:
                        cpu_pct = (1 - idle_diff / total_diff) * 100
                    else:
                        cpu_pct = 0
                else:
                    cpu_pct = 0
            else:
                cpu_pct = 0
            _prev_cpu[key] = {'time': now, 'idle': cpu_idle_total, 'total': cpu_total}

            mem_total = m.get('mem_total', 1)
            mem_avail = m.get('mem_available', 0)
            mem_used = mem_total - mem_avail
            mem_pct = (mem_used / mem_total) * 100 if mem_total > 0 else 0

            disk_used = disk_size - disk_avail
            disk_pct = (disk_used / disk_size) * 100 if disk_size > 0 else 0

            prev_net = _prev_net.get(key)
            if prev_net:
                dt = now - prev_net['time']
                if dt > 0:
                    net_in_rate = (net_rx - prev_net['rx']) / dt
                    net_out_rate = (net_tx - prev_net['tx']) / dt
                else:
                    net_in_rate = 0
                    net_out_rate = 0
            else:
                net_in_rate = 0
                net_out_rate = 0
            _prev_net[key] = {'time': now, 'rx': net_rx, 'tx': net_tx}

            uptime = now - m.get('boot_time', now)

            results[key] = {
                'cpu_percent': round(max(0, min(100, cpu_pct)), 1),
                'cpu_count': cpu_count,
                'mem_percent': round(mem_pct, 1),
                'mem_total': mem_total,
                'mem_used': mem_used,
                'disk_percent': round(disk_pct, 1),
                'disk_total': disk_size,
                'disk_used': disk_used,
                'net_in_bytes': round(max(0, net_in_rate), 0),
                'net_out_bytes': round(max(0, net_out_rate), 0),
                'load1': m.get('load1', 0),
                'load5': m.get('load5', 0),
                'load15': m.get('load15', 0),
                'uptime': round(uptime),
            }
        except Exception as e:
            results[key] = {'error': str(e)}

    return JsonResponse(results)


@login_required
def articles_list(request):
    search = request.GET.get('q', '')
    theme_filter = request.GET.get('theme', '')
    sort = request.GET.get('sort', '-date_publication')

    qs = PgArticle.objects.only(
        'id', 'titre', 'sous_titre', 'theme', 'auteur_full_name',
        'date_publication', 'access_count', 'slug', 'photo', 'vignette',
    )
    if search:
        qs = qs.filter(
            Q(titre__icontains=search) |
            Q(sous_titre__icontains=search) |
            Q(auteur_full_name__icontains=search)
        )
    if theme_filter:
        qs = qs.filter(theme=theme_filter)

    qs = qs.order_by(sort)

    themes_cache = cache.get('article_themes')
    if themes_cache is None:
        themes_cache = [t for t in PgArticle.objects.values_list('theme', flat=True).distinct().order_by('theme') if t]
        cache.set('article_themes', themes_cache, 600)

    total_views = cache.get('article_total_views')
    if total_views is None:
        try:
            total_views = ArticleView.objects.count()
            cache.set('article_total_views', total_views, 120)
        except Exception:
            total_views = 0

    articles = list(qs[:200])

    context = {
        'articles': articles,
        'search': search,
        'theme_filter': theme_filter,
        'sort': sort,
        'total': len(articles) if len(articles) < 200 else qs.count(),
        'themes': themes_cache,
        'total_views': total_views,
    }
    return render(request, 'dashboard/articles.html', context)


@login_required
def article_detail(request, pk):
    article = get_object_or_404(PgArticle, pk=pk)
    views_count = ArticleView.objects.filter(article=article).count()
    context = {
        'article': article,
        'views_count': views_count,
    }
    return render(request, 'dashboard/article_detail.html', context)


@login_required
@require_POST
def article_delete(request, pk):
    article = get_object_or_404(PgArticle, pk=pk)
    titre = article.titre
    article.delete()
    django_messages.success(request, f"Article '{titre}' supprime.")
    return redirect('dashboard:articles')


@login_required
@require_POST
def article_remove_youtube(request, pk):
    article = get_object_or_404(PgArticle, pk=pk)
    article.youtube_video_id = None
    article.youtube_video_title = None
    article.youtube_video_url = None
    article.youtube_video_embed = None
    article.youtube_video_thumbnail = None
    article.save(update_fields=[
        'youtube_video_id', 'youtube_video_title',
        'youtube_video_url', 'youtube_video_embed',
        'youtube_video_thumbnail',
    ])
    django_messages.success(request, "Lien YouTube supprime.")
    return redirect('dashboard:article_detail', pk=pk)


@login_required
def contabo(request):
    return render(request, 'dashboard/contabo.html')


_contabo_ip_map = None

def _build_contabo_ip_map():
    from django.conf import settings as s
    ip_map = {}
    for _key, _label, _host, _user in s._NE_SERVERS:
        ip_map[_host] = _label
    return ip_map


@login_required
def contabo_api(request):
    global _contabo_ip_map
    if _contabo_ip_map is None:
        _contabo_ip_map = _build_contabo_ip_map()

    try:
        instances = list_instances()
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    result = []
    for inst in instances:
        ip_v4 = ''
        ip_v6 = ''
        ip_cfg = inst.get('ipConfig') or {}
        if ip_cfg.get('v4'):
            ip_v4 = ip_cfg['v4'].get('ip', '')
        if ip_cfg.get('v6'):
            ip_v6 = ip_cfg['v6'].get('ip', '')

        additional_ips = []
        for aip in inst.get('additionalIps', []):
            if aip.get('v4', {}).get('ip'):
                additional_ips.append(aip['v4']['ip'])

        role = _contabo_ip_map.get(ip_v4, '')
        if not role:
            for aip in additional_ips:
                role = _contabo_ip_map.get(aip, '')
                if role:
                    break

        result.append({
            'instanceId': inst.get('instanceId'),
            'name': inst.get('name', ''),
            'displayName': inst.get('displayName', ''),
            'status': inst.get('status', 'unknown'),
            'region': inst.get('region', ''),
            'dataCenter': inst.get('dataCenter', ''),
            'ipV4': ip_v4,
            'ipV6': ip_v6,
            'additionalIps': additional_ips,
            'cpuCores': inst.get('cpuCores', 0),
            'ramMb': inst.get('ramMb', 0),
            'diskMb': inst.get('diskMb', 0),
            'osType': inst.get('osType', ''),
            'productId': inst.get('productId', ''),
            'productName': inst.get('productName', ''),
            'productType': inst.get('productType', ''),
            'createdDate': inst.get('createdDate', ''),
            'role': role,
        })

    return JsonResponse({'instances': result})


@login_required
@require_POST
def contabo_action(request):
    instance_id = request.POST.get('instance_id')
    action = request.POST.get('action')
    if not instance_id or action not in ('start', 'stop', 'restart', 'shutdown'):
        return JsonResponse({'error': 'Invalid parameters'}, status=400)
    try:
        instance_action(int(instance_id), action)
        return JsonResponse({'ok': True, 'action': action, 'instanceId': instance_id})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def contabo_snapshots_api(request, instance_id):
    try:
        snaps = list_snapshots(int(instance_id))
        return JsonResponse({'snapshots': snaps})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def contabo_change_password(request):
    instance_id = request.POST.get('instance_id')
    new_password = request.POST.get('password', '').strip()
    if not instance_id or not new_password:
        return JsonResponse({'error': 'instance_id et password requis'}, status=400)
    if len(new_password) < 8:
        return JsonResponse({'error': 'Le mot de passe doit faire au moins 8 caractères'}, status=400)
    try:
        change_password(int(instance_id), new_password)
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def contabo_reinstall(request):
    instance_id = request.POST.get('instance_id')
    image_id = request.POST.get('image_id', '').strip()
    if not instance_id or not image_id:
        return JsonResponse({'error': 'instance_id et image_id requis'}, status=400)
    try:
        reinstall_os(int(instance_id), image_id)
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def contabo_images_api(request):
    try:
        images = list_images()
        result = []
        for img in images:
            result.append({
                'imageId': img.get('imageId', ''),
                'name': img.get('name', ''),
                'description': img.get('description', ''),
                'osType': img.get('osType', ''),
                'version': img.get('version', ''),
            })
        return JsonResponse({'images': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def terminal(request):
    from dashboard.ssh_terminal import get_server_list
    return render(request, 'dashboard/terminal.html', {'servers': get_server_list()})


@login_required
@require_POST
def terminal_connect(request):
    from dashboard.ssh_terminal import connect
    server_key = request.POST.get('server_key', '')
    password = request.POST.get('password', '').strip() or None
    session_id = f'ssh_{request.session.session_key}_{server_key}'
    try:
        result = connect(session_id, server_key, password=password)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def terminal_exec(request):
    import json as _json
    from dashboard.ssh_terminal import execute
    body = _json.loads(request.body)
    server_key = body.get('server_key', '')
    command = body.get('command', '')
    session_id = f'ssh_{request.session.session_key}_{server_key}'
    result = execute(session_id, command)
    return JsonResponse(result)


@login_required
@require_POST
def terminal_disconnect(request):
    from dashboard.ssh_terminal import disconnect
    server_key = request.POST.get('server_key', '')
    session_id = f'ssh_{request.session.session_key}_{server_key}'
    return JsonResponse(disconnect(session_id))


@login_required
def terminal_read(request):
    from dashboard.ssh_terminal import read_output
    server_key = request.GET.get('server_key', '')
    session_id = f'ssh_{request.session.session_key}_{server_key}'
    return JsonResponse(read_output(session_id))


@login_required
@require_POST
def terminal_ai_chat(request):
    import json as _json
    from dashboard.ai_terminal import chat
    body = _json.loads(request.body)
    server_key = body.get('server_key', '')
    message = body.get('message', '')
    command_output = body.get('command_output')
    session_id = f'ai_{request.session.session_key}_{server_key}'
    try:
        result = chat(session_id, message, command_output=command_output)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def terminal_ai_clear(request):
    from dashboard.ai_terminal import clear_conversation
    server_key = request.POST.get('server_key', '')
    session_id = f'ai_{request.session.session_key}_{server_key}'
    clear_conversation(session_id)
    return JsonResponse({'ok': True})


@login_required
def mailbox(request):
    from dashboard.imap_helper import list_emails, list_folders
    folder = request.GET.get('folder', 'INBOX')
    page = int(request.GET.get('page', 0))
    limit = 30
    error = None
    data = {'total': 0, 'emails': []}
    folders = []
    try:
        folders = list_folders()
        data = list_emails(folder=folder, limit=limit, offset=page * limit)
    except Exception as e:
        error = str(e)
    total_pages = max(1, (data['total'] + limit - 1) // limit)
    context = {
        'emails': data['emails'],
        'total': data['total'],
        'folder': folder,
        'folders': folders,
        'page': page,
        'total_pages': total_pages,
        'error': error,
    }
    return render(request, 'dashboard/mailbox.html', context)


@login_required
def mailbox_read(request, uid):
    from dashboard.imap_helper import get_email
    folder = request.GET.get('folder', 'INBOX')
    try:
        mail = get_email(folder, uid)
        if not mail:
            return JsonResponse({'error': 'Email non trouve'}, status=404)
        return JsonResponse(mail)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def mailbox_delete(request, uid):
    from dashboard.imap_helper import delete_email
    folder = request.POST.get('folder', 'INBOX')
    try:
        delete_email(folder, uid)
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def mailbox_send(request):
    from dashboard.email_helper import send_email
    to = request.POST.get('to', '')
    subject = request.POST.get('subject', '')
    body = request.POST.get('body', '')
    if not to or not subject:
        return JsonResponse({'error': 'Destinataire et sujet requis'}, status=400)
    try:
        html = body.replace('\n', '<br>')
        send_email(to, subject, html, text_body=body)
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def newsletter(request):
    return render(request, 'dashboard/newsletter.html')


@login_required
@require_POST
def newsletter_generate_image(request):
    from dashboard.newsletter_helper import generate_and_upload
    prompt = request.POST.get('prompt', '')
    if not prompt:
        return JsonResponse({'error': 'Prompt requis'}, status=400)
    try:
        url = generate_and_upload(prompt)
        return JsonResponse({'ok': True, 'url': url})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def newsletter_send(request):
    import json as _json
    from dashboard.email_helper import send_newsletter
    body = _json.loads(request.body)
    subject = body.get('subject', '')
    html_body = body.get('html', '')
    recipients = body.get('recipients', [])

    if not subject or not html_body:
        return JsonResponse({'error': 'Sujet et contenu requis'}, status=400)

    if not recipients:
        try:
            emails = list(
                Compte.objects.filter(est_active=True)
                .exclude(email__isnull=True).exclude(email='')
                .values_list('email', flat=True)
            )
            recipients = emails
        except Exception:
            return JsonResponse({'error': 'Aucun destinataire'}, status=400)

    if not recipients:
        return JsonResponse({'error': 'Aucun destinataire'}, status=400)

    result = send_newsletter(recipients, subject, html_body)
    return JsonResponse(result)


@login_required
def newsletter_preview_recipients(request):
    try:
        count = Compte.objects.filter(est_active=True).exclude(email__isnull=True).exclude(email='').count()
        sample = list(
            Compte.objects.filter(est_active=True)
            .exclude(email__isnull=True).exclude(email='')
            .values_list('email', flat=True)[:10]
        )
    except Exception:
        count = 0
        sample = []
    return JsonResponse({'count': count, 'sample': sample})


@login_required
def social_analytics(request):
    from . import linkedin_helper
    return render(request, 'dashboard/social_analytics.html', {
        'linkedin_connected': linkedin_helper.is_token_valid(),
    })


LATE_API_BASE = 'https://zernio.com/api/v1'


def _late_headers():
    from django.conf import settings
    return {'Authorization': f'Bearer {settings.LATE_API_KEY}'}


@login_required
def social_analytics_api(request):
    platform = request.GET.get('platform', 'all')
    sort_by = request.GET.get('sortBy', 'date')
    order = request.GET.get('order', 'desc')
    page = request.GET.get('page', '1')
    limit = request.GET.get('limit', '20')
    from_date = request.GET.get('fromDate', '')
    to_date = request.GET.get('toDate', '')

    params = {
        'platform': platform,
        'sortBy': sort_by,
        'order': order,
        'page': page,
        'limit': limit,
    }
    if from_date:
        params['fromDate'] = from_date
    if to_date:
        params['toDate'] = to_date

    _sa_key = f'social_analytics_{platform}_{sort_by}_{order}_{page}_{limit}_{from_date}_{to_date}'
    _sa_cached = cache.get(_sa_key)
    if _sa_cached is not None:
        return JsonResponse(_sa_cached, safe=False)

    try:
        r = http_requests.get(
            f'{LATE_API_BASE}/analytics',
            headers=_late_headers(),
            params=params,
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        cache.set(_sa_key, data, 120)
        return JsonResponse(data, safe=False)
    except http_requests.RequestException as e:
        return JsonResponse({'error': str(e)}, status=502)


def _cors_response(response):
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


@csrf_exempt
def tracking_event(request):
    if request.method == 'OPTIONS':
        return _cors_response(JsonResponse({}))
    if request.method != 'POST':
        return _cors_response(JsonResponse({'error': 'POST only'}, status=405))
    try:
        body = json.loads(request.body)
        ip = (
            request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            or request.META.get('REMOTE_ADDR')
            or None
        )
        UserEvent.objects.create(
            session_id=body.get('session_id', '')[:64],
            ip_address=ip or None,
            user_agent=(request.META.get('HTTP_USER_AGENT', '') or '')[:500],
            event_type=body.get('event_type', 'registration_step')[:50],
            step=body.get('step'),
            step_name=(body.get('step_name', '') or '')[:100],
            data={k: v for k, v in body.items() if k not in ('session_id', 'event_type', 'step', 'step_name')},
            compte_id=(str(body.get('compte_id', '')) or None),
        )
        return _cors_response(JsonResponse({'ok': True}))
    except Exception as e:
        return _cors_response(JsonResponse({'error': str(e)}, status=400))


@login_required
def user_tracking(request):
    return render(request, 'dashboard/user_tracking.html', {})


@login_required
def user_tracking_api(request):
    section = request.GET.get('section', 'all')
    days = int(request.GET.get('days', '30'))
    exclude_admin = request.GET.get('exclude_admin', '1') == '1'

    _cache_key = f'user_tracking_{section}_{days}_{int(exclude_admin)}'
    _cached = cache.get(_cache_key)
    if _cached is not None:
        return JsonResponse(_cached)

    now = timezone.now()
    since = now - timedelta(days=days)

    try:
        qs = Compte.objects.all()
        if exclude_admin:
            qs = qs.filter(is_admin=False, is_staff=False)

        total = qs.count()
        result = {}

        if section in ('all', 'stats'):
            d7 = now - timedelta(days=7)
            d30 = now - timedelta(days=30)
            result['stats'] = {
                'total': total,
                'new_7d': qs.filter(created_at__gte=d7).count(),
                'new_30d': qs.filter(created_at__gte=d30).count(),
                'verified': qs.filter(is_verified=True).count(),
                'premium': qs.exclude(abonnement='gratuit').exclude(abonnement__isnull=True).count(),
                'with_photo': qs.filter(avatar__isnull=False).exclude(avatar='').count(),
            }

        if section in ('all', 'funnel'):
            STEPS = [
                (1, 'type', 'Choix du type (Amour/Amitié/Libertin)'),
                (2, 'sexe', 'Question : Sexe'),
                (3, 'age', 'Question : Âge'),
                (4, 'cgu', 'CGU + Localisation GPS'),
                (5, 'username', 'Question : Pseudo'),
                (6, 'photo', 'Question : Photo'),
                (7, 'email', 'Email + Vérification'),
                (8, 'complete', 'Compte créé ✓'),
            ]

            event_qs = UserEvent.objects.filter(created_at__gte=since)
            total_sessions = event_qs.values('session_id').distinct().count()

            step_counts = {}
            for item in event_qs.filter(event_type__in=['registration_step', 'registration_complete']).values('step').annotate(n=Count('session_id', distinct=True)):
                step_counts[item['step']] = item['n']

            complete_count = event_qs.filter(event_type='registration_complete').values('session_id').distinct().count()
            step_counts[8] = complete_count

            funnel_steps = []
            base = total_sessions or 1
            for step_num, step_id, step_label in STEPS:
                count = step_counts.get(step_num, 0)
                funnel_steps.append({
                    'step': step_label,
                    'count': count,
                    'pct': round(count / base * 100, 1) if base else 0,
                })

            has_real_data = total_sessions > 0

            if not has_real_data:
                has_photo = qs.filter(avatar__isnull=False).exclude(avatar='').count()
                verified = qs.filter(is_verified=True).count()
                premium = qs.exclude(abonnement='gratuit').exclude(abonnement__isnull=True).count()

                def pct(n):
                    return round(n / total * 100, 1) if total else 0

                funnel_steps = [
                    {'step': '① Choix type (Amour/Amitié/Libertin)', 'count': total, 'pct': 100},
                    {'step': '② Sexe', 'count': total, 'pct': 100},
                    {'step': '③ Âge', 'count': total, 'pct': 100},
                    {'step': '④ CGU + Localisation', 'count': qs.filter(cgu=True).count(), 'pct': pct(qs.filter(cgu=True).count())},
                    {'step': '⑤ Pseudo', 'count': qs.filter(cgu=True).count(), 'pct': pct(qs.filter(cgu=True).count())},
                    {'step': '⑥ Photo', 'count': has_photo, 'pct': pct(has_photo)},
                    {'step': '⑦ Email + Vérification', 'count': total, 'pct': 100},
                    {'step': '⑧ Compte créé ✓', 'count': total, 'pct': 100},
                ]

            result['funnel'] = funnel_steps
            result['funnel_real_data'] = has_real_data

        if section in ('all', 'bots'):
            from django.db.models import Count as DbCount
            suspicious_ips = list(
                Compte.objects.values('email')
                .annotate(n=DbCount('id'))
                .filter(n__gte=1)[:1]
            )
            bot_ips = list(
                UserEvent.objects.filter(created_at__gte=since, ip_address__isnull=False)
                .values('ip_address')
                .annotate(sessions=Count('session_id', distinct=True))
                .filter(sessions__gte=3)
                .order_by('-sessions')[:20]
            )
            result['bot_ips'] = [{'ip': b['ip_address'], 'sessions': b['sessions']} for b in bot_ips]

            ip_accounts = list(
                UserEvent.objects.filter(event_type='registration_complete', ip_address__isnull=False)
                .values('ip_address')
                .annotate(comptes=Count('compte_id', distinct=True))
                .filter(comptes__gte=2)
                .order_by('-comptes')[:20]
            )
            result['ip_multi_accounts'] = [{'ip': x['ip_address'], 'comptes': x['comptes']} for x in ip_accounts]

        if section in ('all', 'daily'):
            daily_signups = list(
                qs.filter(created_at__gte=since)
                .annotate(date=TruncDate('created_at'))
                .values('date')
                .annotate(count=Count('id'))
                .order_by('date')
            )
            daily_logins = list(
                qs.filter(last_login__gte=since)
                .annotate(date=TruncDate('last_login'))
                .values('date')
                .annotate(count=Count('id'))
                .order_by('date')
            )
            result['daily_signups'] = [
                {'date': d['date'].strftime('%Y-%m-%d'), 'count': d['count']}
                for d in daily_signups
            ]
            result['daily_logins'] = [
                {'date': d['date'].strftime('%Y-%m-%d'), 'count': d['count']}
                for d in daily_logins
            ]

        if section in ('all', 'retention'):
            d7 = now - timedelta(days=7)
            d30 = now - timedelta(days=30)
            d90 = now - timedelta(days=90)
            result['retention'] = {
                'actif_7j': qs.filter(last_login__gte=d7).count(),
                'actif_30j': qs.filter(last_login__gte=d30, last_login__lt=d7).count(),
                'actif_90j': qs.filter(last_login__gte=d90, last_login__lt=d30).count(),
                'inactif': qs.filter(last_login__lt=d90).count(),
                'jamais_connecte': qs.filter(last_login__isnull=True).count(),
            }

        if section in ('all', 'fields'):
            fields_data = [
                ('Photo', qs.filter(avatar__isnull=False).exclude(avatar='').count()),
                ('Bio', qs.filter(bio__isnull=False).exclude(bio='').count()),
                ('Ville', qs.filter(ville__isnull=False).exclude(ville='').count()),
                ('Téléphone', qs.filter(numberPhone__isnull=False).exclude(numberPhone='').count()),
                ('Date de naissance', qs.filter(date_de_naissance__isnull=False).count()),
                ('Audio', qs.filter(audio__isnull=False).exclude(audio='').count()),
                ('Localisation GPS', qs.filter(latitude__isnull=False).count()),
                ('Taille', qs.filter(taille__isnull=False).count()),
                ('Recherche', qs.filter(recherche__isnull=False).exclude(recherche='').count()),
                ('Métier', qs.filter(metier__isnull=False).exclude(metier='').count()),
                ('Religion', qs.filter(religion__isnull=False).exclude(religion='').count()),
                ('Éducation', qs.filter(education__isnull=False).exclude(education='').count()),
            ]
            result['field_completion'] = [
                {'field': f, 'count': c, 'pct': round(c / total * 100, 1) if total else 0}
                for f, c in sorted(fields_data, key=lambda x: x[1], reverse=True)
            ]

        if section in ('all', 'recent'):
            recent = list(
                qs.order_by('-created_at')[:20].values(
                    'id', 'username', 'email', 'sexe', 'ville',
                    'created_at', 'last_login', 'is_verified',
                    'abonnement', 'avatar',
                )
            )
            for r in recent:
                r['id'] = str(r['id'])
                if r['created_at']:
                    r['created_at'] = r['created_at'].strftime('%Y-%m-%d %H:%M')
                if r['last_login']:
                    r['last_login'] = r['last_login'].strftime('%Y-%m-%d %H:%M')
            result['recent'] = recent

        cache.set(_cache_key, result, 300)
        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def linkedin_connect(request):
    from . import linkedin_helper
    from django.conf import settings
    redirect_uri = settings.LINKEDIN_REDIRECT_URI
    auth_url = linkedin_helper.get_auth_url(redirect_uri)
    from django.shortcuts import redirect as django_redirect
    return django_redirect(auth_url)


@login_required
def linkedin_callback(request):
    from . import linkedin_helper
    from django.conf import settings
    from django.shortcuts import redirect as django_redirect
    error = request.GET.get('error')
    if error:
        return render(request, 'dashboard/social_analytics.html', {
            'linkedin_connected': False,
            'linkedin_error': request.GET.get('error_description', error),
        })
    code = request.GET.get('code', '')
    redirect_uri = settings.LINKEDIN_REDIRECT_URI
    try:
        token_data = linkedin_helper.exchange_code_for_token(code, redirect_uri)
        linkedin_helper.save_token(token_data)
    except Exception as e:
        return render(request, 'dashboard/social_analytics.html', {
            'linkedin_connected': False,
            'linkedin_error': str(e),
        })
    return django_redirect('/social-analytics/')
