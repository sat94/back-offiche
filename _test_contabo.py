import imaplib
import email
from email.header import decode_header

imap = imaplib.IMAP4_SSL('pro3.mail.ovh.net', 993)
imap.login('Admin@meet-voice.fr', 'Pegase1977')
print("Login OK")

status, folders = imap.list()
print("\n=== DOSSIERS ===")
for f in folders:
    print(" ", f.decode())

imap.select('INBOX')
status, messages = imap.search(None, 'ALL')
msg_ids = messages[0].split()
print(f"\n=== INBOX: {len(msg_ids)} emails ===")

for mid in msg_ids[-5:]:
    status, data = imap.fetch(mid, '(RFC822)')
    msg = email.message_from_bytes(data[0][1])
    subject = decode_header(msg['Subject'])[0]
    subj_text = subject[0].decode(subject[1] or 'utf-8') if isinstance(subject[0], bytes) else subject[0]
    from_ = msg['From']
    date_ = msg['Date']
    print(f"  [{mid.decode()}] {date_} | {from_} | {subj_text}")

imap.logout()
