from mollie.api.client import Client
from decouple import config

_client = None


def get_client():
    global _client
    if _client is None:
        _client = Client()
        _client.set_api_key(config('MOLLIE_API_KEY'))
    return _client


def list_payments(limit=250):
    c = get_client()
    result = []
    for p in c.payments.list(limit=limit):
        result.append({
            'id': p.id,
            'amount': p.amount,
            'status': p.status,
            'description': p.description or '',
            'method': getattr(p, 'method', None),
            'created_at': p.created_at,
            'paid_at': getattr(p, 'paid_at', None),
            'customer_id': getattr(p, 'customer_id', None),
            'metadata': getattr(p, 'metadata', None),
            'profile_id': getattr(p, 'profile_id', None),
        })
    return result


def list_customers(limit=250):
    c = get_client()
    result = []
    for cust in c.customers.list(limit=limit):
        result.append({
            'id': cust.id,
            'name': cust.name or '',
            'email': cust.email or '',
            'created_at': cust.created_at,
            'metadata': getattr(cust, 'metadata', None),
        })
    return result


def get_customer_detail(customer_id):
    c = get_client()
    cust = c.customers.get(customer_id)
    payments = []
    for p in c.payments.list(limit=250):
        if getattr(p, 'customer_id', None) == customer_id:
            payments.append({
                'id': p.id,
                'amount': p.amount,
                'status': p.status,
                'description': p.description or '',
                'created_at': p.created_at,
            })

    subs = []
    try:
        for s in c.subscriptions.with_parent_id(customer_id).list():
            subs.append({
                'id': s.id,
                'amount': s.amount,
                'status': s.status,
                'interval': getattr(s, 'interval', ''),
                'description': getattr(s, 'description', ''),
                'created_at': s.created_at,
                'canceled_at': getattr(s, 'canceled_at', None),
                'next_payment_date': getattr(s, 'next_payment_date', None),
            })
    except Exception:
        pass

    return {
        'id': cust.id,
        'name': cust.name or '',
        'email': cust.email or '',
        'created_at': cust.created_at,
        'payments': payments,
        'subscriptions': subs,
    }


def list_all_subscriptions():
    c = get_client()
    result = []
    for cust in c.customers.list(limit=250):
        try:
            for s in c.subscriptions.with_parent_id(cust.id).list():
                result.append({
                    'id': s.id,
                    'customer_id': cust.id,
                    'customer_name': cust.name or '',
                    'customer_email': cust.email or '',
                    'amount': s.amount,
                    'status': s.status,
                    'interval': getattr(s, 'interval', ''),
                    'description': getattr(s, 'description', ''),
                    'created_at': s.created_at,
                    'canceled_at': getattr(s, 'canceled_at', None),
                    'next_payment_date': getattr(s, 'next_payment_date', None),
                })
        except Exception:
            pass
    return result


def list_refunds(limit=250):
    c = get_client()
    result = []
    for r in c.refunds.list(limit=limit):
        result.append({
            'id': r.id,
            'amount': r.amount,
            'status': r.status,
            'payment_id': getattr(r, 'payment_id', ''),
            'created_at': r.created_at,
            'description': getattr(r, 'description', ''),
        })
    return result


def create_refund(payment_id, amount=None):
    c = get_client()
    payment = c.payments.get(payment_id)
    data = {}
    if amount:
        data['amount'] = {'currency': 'EUR', 'value': str(amount)}
    return c.payment_refunds.with_parent_id(payment_id).create(data)


def cancel_subscription(customer_id, subscription_id):
    c = get_client()
    c.subscriptions.with_parent_id(customer_id).delete(subscription_id)


def list_methods():
    c = get_client()
    result = []
    for m in c.methods.list():
        result.append({
            'id': m.id,
            'description': m.description,
        })
    return result


def get_stats():
    payments = list_payments()
    customers = list_customers()
    subscriptions = list_all_subscriptions()

    total_paid = sum(
        float(p['amount']['value'])
        for p in payments if p['status'] == 'paid'
    )
    total_pending = sum(
        float(p['amount']['value'])
        for p in payments if p['status'] in ('open', 'pending')
    )
    active_subs = [s for s in subscriptions if s['status'] == 'active']

    return {
        'total_payments': len(payments),
        'paid_count': sum(1 for p in payments if p['status'] == 'paid'),
        'failed_count': sum(1 for p in payments if p['status'] == 'failed'),
        'total_paid': total_paid,
        'total_pending': total_pending,
        'total_customers': len(customers),
        'total_subscriptions': len(subscriptions),
        'active_subscriptions': len(active_subs),
        'currency': 'EUR',
    }
