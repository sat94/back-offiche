import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from decouple import config


def send_email(to_email, subject, html_body, text_body=None):
    host = config('SMTP_HOST')
    port = config('SMTP_PORT', cast=int)
    user = config('SMTP_USER')
    password = config('SMTP_PASSWORD')
    from_email = config('SMTP_FROM_EMAIL')
    from_name = config('SMTP_FROM_NAME', default='MeetVoice')

    msg = MIMEMultipart('alternative')
    msg['From'] = f'{from_name} <{from_email}>'
    msg['To'] = to_email
    msg['Subject'] = subject

    if text_body:
        msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    with smtplib.SMTP(host, port, timeout=15) as server:
        server.starttls()
        server.login(user, password)
        server.send_message(msg)


def send_admin_alert(subject, html_body):
    admin_email = config('SMTP_FROM_EMAIL')
    send_email(admin_email, f'[MeetVoice Admin] {subject}', html_body)


def send_newsletter(recipients, subject, html_body):
    results = {'sent': 0, 'failed': 0, 'errors': []}
    for email in recipients:
        try:
            send_email(email, subject, html_body)
            results['sent'] += 1
        except Exception as e:
            results['failed'] += 1
            results['errors'].append(f'{email}: {str(e)}')
    return results
