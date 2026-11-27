"""Send a product news / offers email to the "offers" subscribers.

The email is a Markdown file in emails/. First lines are headers, then a blank line, then the body:

    Subject: New Makita tool wall mounts
    Preview: Short line shown in the inbox next to the subject (optional)

    Hi there,
    ...

Usage:
    python send_offer_email.py emails/2026-12-makita.md test   # only to the Quality3Ds Gmail inbox
    python send_offer_email.py emails/2026-12-makita.md all    # every confirmed offers subscriber
"""
import os
import re
import sys

import markdown

import subscriber_mail as mail

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SENT_LOG = os.path.join(PROJECT_ROOT, "emails", "sent.txt")


def load_email(path):
    with open(path, encoding="utf-8") as handle:
        raw = handle.read().replace("\r\n", "\n")
    head, _, body = raw.partition("\n\n")
    headers = {}
    for line in head.splitlines():
        key, sep, value = line.partition(":")
        if sep:
            headers[key.strip().lower()] = value.strip()
    subject = headers.get("subject", "")
    if not subject or not body.strip():
        raise SystemExit(f"{path}: needs a 'Subject:' line, a blank line, then the email text.")
    inner_html = markdown.markdown(body, extensions=["extra"])
    # Gmail strips <style>; give links and images inline styles.
    inner_html = inner_html.replace("<a ", f'<a style="color:{mail.TEAL}" ')
    inner_html = re.sub(r"<img ", '<img style="max-width:100%;height:auto;border-radius:8px" ', inner_html)
    return subject, headers.get("preview", ""), inner_html, body


def already_sent(name):
    if not os.path.exists(SENT_LOG):
        return False
    with open(SENT_LOG, encoding="utf-8") as handle:
        return name in {line.strip() for line in handle}


def main(argv, fetch=mail.fetch_subscribers, send=mail.send_all):
    if len(argv) != 3 or argv[2] not in ("test", "all"):
        raise SystemExit(__doc__)
    path, mode = argv[1], argv[2]
    name = os.path.relpath(os.path.abspath(path), PROJECT_ROOT).replace("\\", "/")
    subject, preview, inner_html, text = load_email(path)
    settings = mail.gmail_settings()
    if not settings:
        raise SystemExit("Gmail settings are not set (PULSE_EMAIL_GMAIL_USER / PULSE_EMAIL_GMAIL_APP_PASSWORD).")
    if mode == "test":
        recipients = [{"email": settings[0], "token": "test"}]
        subject = "[TEST] " + subject
    else:
        if already_sent(name):
            raise SystemExit(f"{name} was already sent to everyone. Copy it to a new file to send again.")
        recipients = fetch("offers")
        print(f"Offers subscribers: {len(recipients)}")
    sent, failed = send(recipients, "offers", subject, inner_html, text, preheader=preview)
    if mode == "all" and sent:
        os.makedirs(os.path.dirname(SENT_LOG), exist_ok=True)
        with open(SENT_LOG, "a", encoding="utf-8", newline="\n") as handle:
            handle.write(name + "\n")
    return 0 if sent or not recipients else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
