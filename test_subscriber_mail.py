import os
import smtplib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import send_offer_email as offer
import send_pulse_email as pulse
import subscriber_mail as mail

ISSUE = """# Quality3Ds Daily 3D Printing News - 2026-11-28

## Stories

🚨 Bambu Lab introduces the S1 3D scanner
The S1 is a handheld scanner.
Reported by Bambu Lab on Nov 27, 2026.
Image ? https://img.test/s1.jpg
Read more ? https://news.test/s1

📷 Second story about scanners <b>bold</b>
Some detail.
Read more ? https://news.test/two
"""
GMAIL = {"PULSE_EMAIL_GMAIL_USER": "shop@gmail.test", "PULSE_EMAIL_GMAIL_APP_PASSWORD": "app-pass", "SUBSCRIBER_EXPORT_TOKEN": "t" * 40}
SUBS = [{"email": "a@x.test", "token": "a" * 48}, {"email": "b@x.test", "token": "b" * 48}]


class FakeSMTP:
    instances = []

    def __init__(self, fail_first=0):
        self.sent, self.fail_first = [], fail_first
        FakeSMTP.instances.append(self)

    def login(self, user, password):
        self.user = user

    def send_message(self, message):
        if self.fail_first:
            self.fail_first -= 1
            raise smtplib.SMTPServerDisconnected("drop")
        self.sent.append(message)

    def quit(self):
        pass

    close = quit


class SubscriberMailTests(unittest.TestCase):
    def setUp(self):
        FakeSMTP.instances = []

    def test_issue_parsing_and_render_escape_html(self):
        stories = pulse.parse_issue(ISSUE)
        self.assertEqual([s["url"] for s in stories], ["https://news.test/s1", "https://news.test/two"])
        self.assertEqual(stories[0]["image"], "https://img.test/s1.jpg")
        subject, inner, text = pulse.render(stories, "2026-11-28")
        self.assertIn("2026-11-28", subject)
        self.assertIn("&lt;b&gt;bold&lt;/b&gt;", inner)
        self.assertIn("Read more: https://news.test/two", text)

    def test_each_message_has_its_own_unsubscribe(self):
        msg = mail.build_message("shop@gmail.test", SUBS[0], "pulse", "Subj", "<p>Hi</p>", "Hi")
        self.assertEqual(msg["To"], "a@x.test")
        self.assertIn("t=" + "a" * 48, msg["List-Unsubscribe"])
        self.assertIn("list=pulse", msg["List-Unsubscribe"])
        self.assertEqual(msg["List-Unsubscribe-Post"], "List-Unsubscribe=One-Click")
        html_part = msg.get_body(("html",)).get_content()
        text_part = msg.get_body(("plain",)).get_content()
        self.assertIn("Unsubscribe", html_part)
        self.assertIn("New Plymouth", text_part)

    def test_send_all_reconnects_after_a_drop_and_counts(self):
        with patch.dict(os.environ, GMAIL):
            sent, failed = mail.send_all(SUBS, "pulse", "S", "<p>x</p>", "x",
                                         smtp_factory=lambda: FakeSMTP(fail_first=1 if not FakeSMTP.instances else 0),
                                         sleep=lambda s: None)
        self.assertEqual((sent, failed), (2, 0))
        self.assertEqual(len(FakeSMTP.instances), 2)

    def test_send_all_without_gmail_settings_sends_nothing(self):
        with patch.dict(os.environ, {"PULSE_EMAIL_GMAIL_USER": "", "PULSE_EMAIL_GMAIL_APP_PASSWORD": ""}):
            self.assertEqual(mail.send_all(SUBS, "pulse", "S", "x", "x", smtp_factory=FakeSMTP), (0, 0))
        self.assertEqual(FakeSMTP.instances, [])

    def test_send_all_caps_at_the_daily_limit(self):
        with patch.dict(os.environ, GMAIL), patch.object(mail, "MAX_PER_RUN", 1):
            sent, _ = mail.send_all(SUBS, "pulse", "S", "x", "x", smtp_factory=FakeSMTP, sleep=lambda s: None)
        self.assertEqual(sent, 1)

    def test_pulse_is_emailed_once_per_issue(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, GMAIL), \
                patch.object(pulse, "PROJECT_ROOT", tmp), patch.object(pulse, "MARKER_FILE", os.path.join(tmp, "m.txt")):
            Path(tmp, "2026-11-28").mkdir()
            Path(tmp, "2026-11-28", "README.md").write_text(ISSUE, encoding="utf-8")
            calls = []
            send = lambda subs, list_name, *rest, **kw: calls.append((len(subs), list_name)) or (len(subs), 0)
            self.assertEqual(pulse.main("2026-11-28", fetch=lambda name: SUBS, send=send), 0)
            self.assertEqual(pulse.main("2026-11-28", fetch=lambda name: SUBS, send=send), 0)
            self.assertEqual(calls, [(2, "pulse")])
            # No issue for a later day (daily build failed): nothing is sent.
            self.assertEqual(pulse.main("2026-11-29", fetch=lambda name: SUBS, send=send), 0)
            self.assertEqual(len(calls), 1)

    def test_offer_test_mode_goes_only_to_the_shop_inbox_and_all_mode_only_once(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, GMAIL), \
                patch.object(offer, "PROJECT_ROOT", tmp), patch.object(offer, "SENT_LOG", os.path.join(tmp, "emails", "sent.txt")):
            Path(tmp, "emails").mkdir()
            path = Path(tmp, "emails", "deal.md")
            path.write_text("Subject: Big deal\nPreview: Short\n\nHello **there** [shop](https://www.quality3ds.com)\n", encoding="utf-8")
            calls = []
            send = lambda subs, list_name, subject, inner, text, preheader="": calls.append((subs, list_name, subject, inner)) or (len(subs), 0)
            offer.main(["x", str(path), "test"], fetch=lambda name: self.fail("test mode must not fetch"), send=send)
            self.assertEqual(calls[0][0], [{"email": "shop@gmail.test", "token": "test"}])
            self.assertEqual(calls[0][2], "[TEST] Big deal")
            self.assertIn("<strong>there</strong>", calls[0][3])
            offer.main(["x", str(path), "all"], fetch=lambda name: SUBS, send=send)
            self.assertEqual((calls[1][1], len(calls[1][0])), ("offers", 2))
            with self.assertRaises(SystemExit):
                offer.main(["x", str(path), "all"], fetch=lambda name: SUBS, send=send)

    def test_offer_file_needs_subject_and_body(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "bad.md")
            path.write_text("Hello with no subject\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                offer.load_email(str(path))


if __name__ == "__main__":
    unittest.main()
