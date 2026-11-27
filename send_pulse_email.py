"""Email today's Pulse issue to the "pulse" subscribers (runs after auto_daily.py).

Sends only when today's issue exists and hasn't been emailed yet
(last_emailed_issue.txt holds the last date sent). Prints counts only.
"""
import datetime
import html
import os
import re
import sys

import subscriber_mail as mail
from generate_rss import calculate_pulse_number

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
MARKER_FILE = os.path.join(PROJECT_ROOT, "last_emailed_issue.txt")


def parse_issue(markdown_text):
    """Turn a daily README into a list of stories: title, lines, image, url."""
    body = markdown_text.split("## Stories", 1)[-1]
    stories = []
    for block in re.split(r"\n\s*\n", body.strip()):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines or lines[0].startswith("#"):
            continue
        story = {"title": lines[0], "lines": [], "image": "", "url": ""}
        for line in lines[1:]:
            link = re.search(r"https?://\S+", line)
            if line.startswith("Read more") and link:
                story["url"] = link.group(0)
            elif line.startswith("Image") and link:
                story["image"] = link.group(0)
            else:
                story["lines"].append(line)
        if story["url"]:
            stories.append(story)
    return stories


def render(stories, date_str):
    number = calculate_pulse_number(datetime.datetime.strptime(date_str, "%Y-%m-%d").date())
    subject = f"3D Printing Pulse #{number} - {date_str}"
    parts = [f'<h1 style="font-size:22px;margin:0 0 4px">3D Printing Pulse #{number}</h1>'
             f'<p style="margin:0 0 18px;color:#6b7280">{html.escape(date_str)} &middot; today\'s top 3D printing stories</p>']
    text = [subject, ""]
    for story in stories:
        title = html.escape(story["title"])
        url = html.escape(story["url"])
        image = (f'<img src="{html.escape(story["image"])}" alt="" width="120" '
                 'style="float:right;margin:0 0 8px 12px;border-radius:6px;max-width:120px">') if story["image"] else ""
        summary = " ".join(html.escape(line) for line in story["lines"][:2])
        parts.append(f'<div style="margin:0 0 20px;padding:0 0 16px;border-bottom:1px solid #e5e7eb;overflow:hidden">{image}'
                     f'<a href="{url}" style="color:#111827;font-weight:bold;font-size:16px;text-decoration:none">{title}</a>'
                     f'<p style="margin:6px 0 8px;color:#374151">{summary}</p>'
                     f'<a href="{url}" style="color:{mail.TEAL}">Read more &rarr;</a></div>')
        text += [story["title"], *story["lines"][:2], f"Read more: {story['url']}", ""]
    parts.append(f'<p style="margin:8px 0 0"><a href="{mail.SITE}/news-pulse.html" style="color:{mail.TEAL}">See the Pulse on our website</a></p>')
    return subject, "".join(parts), "\n".join(text)


def main(today=None, fetch=mail.fetch_subscribers, send=mail.send_all):
    today = today or datetime.datetime.now().strftime("%Y-%m-%d")
    issue_path = os.path.join(PROJECT_ROOT, today, "README.md")
    if not os.path.exists(issue_path):
        print(f"No issue for {today}; nothing to email.")
        return 0
    if os.path.exists(MARKER_FILE) and open(MARKER_FILE, encoding="utf-8").read().strip() == today:
        print(f"Issue {today} was already emailed.")
        return 0
    if not mail.gmail_settings() or not os.getenv("SUBSCRIBER_EXPORT_TOKEN", "").strip():
        print("Subscriber email skipped: Gmail or subscriber-list secrets are not set.")
        return 0
    with open(issue_path, encoding="utf-8") as handle:
        stories = parse_issue(handle.read())
    if not stories:
        print(f"Issue {today} has no stories; nothing to email.")
        return 0
    subscribers = fetch("pulse")
    print(f"Pulse subscribers: {len(subscribers)}")
    if subscribers:
        subject, inner_html, text = render(stories, today)
        sent, failed = send(subscribers, "pulse", subject, inner_html, text, preheader=stories[0]["title"])
        if failed and not sent:
            print("Every send failed; not marking the issue as emailed.", file=sys.stderr)
            return 1
    with open(MARKER_FILE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(today + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
