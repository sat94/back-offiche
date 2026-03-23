import imaplib
import email
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime
from decouple import config


def _decode_header_value(value):
    if not value:
        return ''
    parts = decode_header(value)
    result = []
    for data, charset in parts:
        if isinstance(data, bytes):
            result.append(data.decode(charset or 'utf-8', errors='replace'))
        else:
            result.append(data)
    return ''.join(result)


def _get_body(msg):
    html_body = None
    text_body = None

    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            disp = str(part.get('Content-Disposition', ''))
            if 'attachment' in disp:
                continue
            if ct == 'text/html' and html_body is None:
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or 'utf-8'
                html_body = payload.decode(charset, errors='replace')
            elif ct == 'text/plain' and text_body is None:
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or 'utf-8'
                text_body = payload.decode(charset, errors='replace')
    else:
        payload = msg.get_payload(decode=True)
        charset = msg.get_content_charset() or 'utf-8'
        ct = msg.get_content_type()
        decoded = payload.decode(charset, errors='replace') if payload else ''
        if ct == 'text/html':
            html_body = decoded
        else:
            text_body = decoded

    return html_body or text_body or ''


def _get_attachments(msg):
    attachments = []
    if not msg.is_multipart():
        return attachments
    for part in msg.walk():
        disp = str(part.get('Content-Disposition', ''))
        if 'attachment' in disp:
            filename = part.get_filename()
            if filename:
                filename = _decode_header_value(filename)
            size = len(part.get_payload(decode=True) or b'')
            attachments.append({
                'filename': filename or 'sans-nom',
                'size': size,
                'content_type': part.get_content_type(),
            })
    return attachments


def _connect():
    host = config('SMTP_HOST')
    user = config('SMTP_USER')
    password = config('SMTP_PASSWORD')
    imap = imaplib.IMAP4_SSL(host, 993)
    imap.login(user, password)
    return imap


def list_folders():
    imap = _connect()
    try:
        status, folders = imap.list()
        result = []
        for f in folders:
            parts = f.decode().split('"/"')
            if len(parts) >= 2:
                name = parts[-1].strip().strip('"')
                result.append(name)
        return result
    finally:
        imap.logout()


def list_emails(folder='INBOX', limit=50, offset=0):
    imap = _connect()
    try:
        imap.select(folder, readonly=True)
        status, messages = imap.search(None, 'ALL')
        msg_ids = messages[0].split()
        total = len(msg_ids)

        msg_ids = list(reversed(msg_ids))
        page = msg_ids[offset:offset + limit]

        result = []
        for mid in page:
            status, data = imap.fetch(mid, '(FLAGS BODY.PEEK[HEADER.FIELDS (FROM TO SUBJECT DATE)])')
            if not data or not data[0]:
                continue

            flags_raw = data[0][0] if isinstance(data[0], tuple) else b''
            is_seen = b'\\Seen' in flags_raw

            header_data = data[0][1] if isinstance(data[0], tuple) else data[0]
            msg = email.message_from_bytes(header_data)

            from_name, from_email = parseaddr(msg['From'] or '')
            from_display = _decode_header_value(from_name) or from_email

            try:
                date = parsedate_to_datetime(msg['Date'])
                date_str = date.strftime('%d/%m/%Y %H:%M')
            except Exception:
                date_str = msg.get('Date', '')

            result.append({
                'uid': mid.decode(),
                'from_name': from_display,
                'from_email': from_email,
                'to': _decode_header_value(msg.get('To', '')),
                'subject': _decode_header_value(msg.get('Subject', '(sans sujet)')),
                'date': date_str,
                'is_read': is_seen,
            })

        return {'total': total, 'emails': result}
    finally:
        imap.logout()


def get_email(folder, uid):
    imap = _connect()
    try:
        imap.select(folder)
        status, data = imap.fetch(uid.encode(), '(RFC822)')
        if not data or not data[0]:
            return None

        msg = email.message_from_bytes(data[0][1])

        from_name, from_email = parseaddr(msg['From'] or '')
        from_display = _decode_header_value(from_name) or from_email

        try:
            date = parsedate_to_datetime(msg['Date'])
            date_str = date.strftime('%d/%m/%Y %H:%M')
        except Exception:
            date_str = msg.get('Date', '')

        to_list = []
        if msg['To']:
            for addr in msg['To'].split(','):
                name, em = parseaddr(addr.strip())
                to_list.append(_decode_header_value(name) or em)

        return {
            'uid': uid,
            'from_name': from_display,
            'from_email': from_email,
            'to': to_list,
            'subject': _decode_header_value(msg.get('Subject', '(sans sujet)')),
            'date': date_str,
            'body': _get_body(msg),
            'attachments': _get_attachments(msg),
        }
    finally:
        imap.logout()


def delete_email(folder, uid):
    imap = _connect()
    try:
        imap.select(folder)
        imap.store(uid.encode(), '+FLAGS', '\\Deleted')
        imap.expunge()
    finally:
        imap.logout()
