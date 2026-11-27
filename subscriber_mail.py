"""Send emails to Quality3Ds newsletter subscribers through Gmail.

Subscribers sign up on www.quality3ds.com; the site's Worker keeps the list and
hands it to this script at /subscribe/list (needs SUBSCRIBER_EXPORT_TOKEN).
Every email gets the person's own unsubscribe link and one-click unsubscribe
headers. This repo is public: never print email addresses or tokens.
"""
import html
import json
import os
import smtplib
import sys
import time
import urllib.parse
import urllib.request
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

SITE = "https://www.quality3ds.com"
LIST_URL = os.getenv("SUBSCRIBER_API_URL", SITE + "/subscribe/list")
# Personal Gmail accepts roughly 500 recipients a day; leave room for normal mail.
MAX_PER_RUN = int(os.getenv("SUBSCRIBER_MAX_PER_RUN", "450"))
SEND_DELAY_SECONDS = float(os.getenv("SUBSCRIBER_SEND_DELAY_SECONDS", "1"))
LIST_LABELS = {
    "pulse": "the Quality3Ds daily 3D printing news pulse",
    "offers": "Quality3Ds product news and offers",
}
TEAL = "#1B8A83"


def gmail_settings():
    user = os.getenv("PULSE_EMAIL_GMAIL_USER", "").strip()
    password = os.getenv("PULSE_EMAIL_GMAIL_APP_PASSWORD", "").strip()
    if not user or not password:
        return None
    return user, password


def fetch_subscribers(list_name, token=None, opener=urllib.request.urlopen):
    token = token if token is not None else os.getenv("SUBSCRIBER_EXPORT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("SUBSCRIBER_EXPORT_TOKEN is not set.")
    url = LIST_URL + "?" + urllib.parse.urlencode({"list": list_name})
    request = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + token,
        "User-Agent": "Quality3DsPulseMailer/1.0",
        "Accept": "application/json",
    })
    last_error = None
    for attempt in range(3):
        try:
            with opener(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
            return [s for s in data.get("subscribers", []) if s.get("email") and s.get("token")]
        except Exception as exc:  # retry network blips with backoff
            last_error = exc
            time.sleep(2 ** attempt * 3)
    raise RuntimeError(f"Could not fetch the subscriber list: {type(last_error).__name__}")


def unsubscribe_url(token, list_name):
    return f"{SITE}/subscribe/unsubscribe?" + urllib.parse.urlencode({"t": token, "list": list_name})


def wrap_html(inner_html, list_name, unsub_url, preheader=""):
    why = html.escape(LIST_LABELS[list_name])
    pre = f'<div style="display:none;max-height:0;overflow:hidden">{html.escape(preheader)}</div>' if preheader else ""
    return f"""<!doctype html><html><body style="margin:0;padding:0;background:#f3f4f6">{pre}
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:640px;background:#ffffff;border-radius:12px;font-family:Arial,Helvetica,sans-serif;color:#1f2937;font-size:15px;line-height:1.55">
<tr><td style="padding:22px 28px;border-bottom:3px solid {TEAL}"><a href="{SITE}" style="color:{TEAL};font-size:20px;font-weight:bold;text-decoration:none">Quality3Ds</a>
<div style="color:#6b7280;font-size:13px">Think It, Make It!</div></td></tr>
<tr><td style="padding:22px 28px">{inner_html}</td></tr>
<tr><td style="padding:18px 28px;border-top:1px solid #e5e7eb;color:#6b7280;font-size:12px;line-height:1.5">
You're getting this because you subscribed to {why} at quality3ds.com.<br>
<a href="{html.escape(unsub_url)}" style="color:#6b7280">Unsubscribe</a> &middot; Quality3Ds, New Plymouth, New Zealand &middot; <a href="{SITE}" style="color:#6b7280">quality3ds.com</a>
</td></tr></table></td></tr></table></body></html>"""


def wrap_text(text_body, list_name, unsub_url):
    return (f"{text_body.strip()}\n\n--\nYou're getting this because you subscribed to "
            f"{LIST_LABELS[list_name]} at quality3ds.com.\nUnsubscribe: {unsub_url}\n"
            "Quality3Ds, New Plymouth, New Zealand - https://www.quality3ds.com\n")


def build_message(sender, subscriber, list_name, subject, inner_html, text_body, preheader=""):
    unsub = unsubscribe_url(subscriber["token"], list_name)
    msg = EmailMessage()
    msg["From"] = formataddr(("Quality3Ds", sender))
    msg["To"] = subscriber["email"]
    msg["Subject"] = subject
    msg["Message-ID"] = make_msgid(domain="quality3ds.com")
    msg["List-Unsubscribe"] = f"<{unsub}>"
    msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    msg.set_content(wrap_text(text_body, list_name, unsub))
    msg.add_alternative(wrap_html(inner_html, list_name, unsub, preheader), subtype="html")
    return msg


def send_all(subscribers, list_name, subject, inner_html, text_body, preheader="", smtp_factory=None, sleep=time.sleep):
    """Send one email per subscriber. Returns (sent, failed). Prints counts only."""
    settings = gmail_settings()
    if not settings:
        print("Subscriber email skipped: Gmail settings are not set.")
        return 0, 0
    user, password = settings
    if len(subscribers) > MAX_PER_RUN:
        print(f"WARNING: {len(subscribers)} subscribers but only {MAX_PER_RUN} are sent per run "
              "(Gmail daily limit). Time to move to a newsletter service.", file=sys.stderr)
        subscribers = subscribers[:MAX_PER_RUN]
    factory = smtp_factory or (lambda: smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30))
    sent = failed = 0
    smtp = None
    try:
        for index, subscriber in enumerate(subscribers):
            message = build_message(user, subscriber, list_name, subject, inner_html, text_body, preheader)
            for attempt in range(2):
                try:
                    if smtp is None:
                        smtp = factory()
                        smtp.login(user, password)
                    smtp.send_message(message)
                    sent += 1
                    break
                except smtplib.SMTPRecipientsRefused:
                    failed += 1
                    break
                except (smtplib.SMTPException, OSError) as exc:
                    try:
                        if smtp is not None:
                            smtp.close()
                    except Exception:
                        pass
                    smtp = None
                    if attempt == 1:
                        failed += 1
                        print(f"Send failed for subscriber #{index + 1}: {type(exc).__name__}", file=sys.stderr)
                    else:
                        sleep(5)
            if index + 1 < len(subscribers):
                sleep(SEND_DELAY_SECONDS)
    finally:
        if smtp is not None:
            try:
                smtp.quit()
            except Exception:
                pass
    print(f"Subscriber email: {sent} sent, {failed} failed ({list_name} list).")
    return sent, failed
