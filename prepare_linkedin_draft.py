import xml.etree.ElementTree as ET
import os
import re
import smtplib
import sys
import time
from email.message import EmailMessage
from urllib.parse import urlparse

MOJIBAKE_MARKERS = (
    "\u00c3",
    "\u00c2",
    "\u00e2\u20ac",
    "\u00f0\u0178",
    "\u00ef\u00bf\u00bd"
)
CP1252_REVERSE = {
    0x20AC: 0x80,
    0x201A: 0x82,
    0x0192: 0x83,
    0x201E: 0x84,
    0x2026: 0x85,
    0x2020: 0x86,
    0x2021: 0x87,
    0x02C6: 0x88,
    0x2030: 0x89,
    0x0160: 0x8A,
    0x2039: 0x8B,
    0x0152: 0x8C,
    0x017D: 0x8E,
    0x2018: 0x91,
    0x2019: 0x92,
    0x201C: 0x93,
    0x201D: 0x94,
    0x2022: 0x95,
    0x2013: 0x96,
    0x2014: 0x97,
    0x02DC: 0x98,
    0x2122: 0x99,
    0x0161: 0x9A,
    0x203A: 0x9B,
    0x0153: 0x9C,
    0x017E: 0x9E,
    0x0178: 0x9F
}

CANONICAL_SITE_URL = "https://www.quality3ds.com/"
LEGACY_SITE_HOSTS = {
    "quality3ds.godaddysites.com",
    "quality3ds.com",
    "www.quality3ds.com",
}
FOCUS_OVERRIDE_BY_DATE = {
    "2026-03-18": {
        "topic": "3D-printed MANPADS launcher under $100",
        "story_url": "https://www.youtube.com/watch?v=DDO2EvXyncE",
        "extra_url": "https://github.com/novatic14/Distributed-Camera-Node-Tracking-System",
    },
}
VIRAL_HINT_KEYWORDS = {
    "viral", "controversy", "controversial", "backlash", "outrage", "lawsuit",
    "ban", "boycott", "scandal", "warning", "firestorm", "criticized",
    "unsafe", "recall", "hepa14", "voc"
}
RECYCLING_HINT_KEYWORDS = {
    "recycling", "recycle", "recycled", "filament recycler", "filament recycling",
    "waste plastic", "closed-loop", "closed loop", "creality m1"
}
MAJOR_RELEASE_BRANDS = {
    "bambu", "prusa", "creality", "elegoo", "ultimaker", "formlabs",
    "snapmaker", "qidi", "raise3d", "anycubic", "ankermake"
}
MAJOR_RELEASE_TERMS = {
    "launch", "launches", "launched", "reveal", "reveals", "revealed",
    "announce", "announces", "announced", "introduce", "introduces",
    "introduced", "unveil", "unveils", "unveiled", "new printer",
    "next-gen", "next generation", "flagship"
}
DAILY_FOCUS_TEMPLATES = [
    'Today\'s pulse highlight is "{topic}" {reason}. Story link: {story_url} | Full pulse: {url}',
    'If you only open one story from today, make it "{topic}" {reason}. Direct link: {story_url} | Full coverage: {url}',
    'The story setting the tone today is "{topic}" {reason}. Read it here: {story_url} | Full pulse: {url}',
    'Today\'s standout topic: "{topic}" {reason}. Story: {story_url} | Explore more: {url}',
    'Big conversation driver today: "{topic}" {reason}. Source: {story_url} | Complete rundown: {url}',
]
GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 465
DEFAULT_EMAIL_TIMEOUT_SECONDS = 20
DEFAULT_EMAIL_MAX_RETRIES = 3
DEFAULT_EMAIL_RETRY_DELAY_SECONDS = 3

def looks_mojibake(text):
    if not text:
        return False
    return any(marker in text for marker in MOJIBAKE_MARKERS)

def repair_mojibake_chunk(chunk):
    if not looks_mojibake(chunk):
        return chunk

    output = []
    for ch in chunk:
        code = ord(ch)
        if code <= 0xFF:
            output.append(ch)
        elif code in CP1252_REVERSE:
            output.append(chr(CP1252_REVERSE[code]))
        else:
            return chunk

    try:
        repaired = "".join(output).encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return chunk
    if looks_mojibake(repaired):
        return chunk
    return repaired

def fix_mojibake(text):
    if not text or not looks_mojibake(text):
        return text

    output = []
    buffer = []

    def flush_buffer():
        if not buffer:
            return
        chunk = "".join(buffer)
        output.append(repair_mojibake_chunk(chunk))
        buffer.clear()

    for ch in text:
        code = ord(ch)
        if code <= 0xFF or code in CP1252_REVERSE:
            buffer.append(ch)
        else:
            flush_buffer()
            output.append(ch)

    flush_buffer()
    return "".join(output)

def clean_html_for_markdown(html_content):
    """
    Converts basic HTML tags from the RSS feed into a clean text/markdown format
    suitable for copying into LinkedIn.
    """
    html_content = fix_mojibake(html_content or "")
    # Replace <p> tags with double newlines for paragraph breaks
    text = re.sub(r'<p>', '', html_content)
    text = re.sub(r'</p>', '\n\n', text)

    # Replace <br> with newline
    text = re.sub(r'<br\s*/?>', '\n', text)

    # Simple clean up of "Read more ?" links to be cleaner
    # (Optional: customize this if you want different formatting)
    text = text.replace('Read more ?', '\U0001F517 Read more:')
    text = text.replace('Image ?', '\U0001F5BC\uFE0F Image:')

    # Remove other potential HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Fix multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return fix_mojibake(text).strip()

def normalize_quality3ds_link(link):
    """
    Rewrites known Quality3Ds legacy links to the canonical site URL.
    """
    link = (link or "").strip()
    if not link:
        return CANONICAL_SITE_URL

    try:
        parsed = urlparse(link)
    except Exception:
        return CANONICAL_SITE_URL

    host = (parsed.netloc or "").lower()
    if host in LEGACY_SITE_HOSTS:
        return CANONICAL_SITE_URL

    return link

def strip_leading_symbols(text):
    return re.sub(r"^[^\w\d]+", "", text or "").strip()

def extract_story_titles(body_content):
    titles = []
    for raw_line in (body_content or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        lower = line.lower()
        if "read more:" in lower or "image:" in lower:
            continue
        if len(line) > 140:
            continue
        if len(line.split()) < 3:
            continue
        if line.endswith("."):
            continue
        titles.append(strip_leading_symbols(line))
    return titles

def extract_read_more_links(body_content):
    links = []
    for raw_line in (body_content or "").splitlines():
        line = raw_line.strip()
        if "read more:" not in line.lower():
            continue
        match = re.search(r"https?://\S+", line)
        if match:
            links.append(match.group(0).rstrip(").,]"))
    return links

def is_story_title_line(line):
    if not line:
        return False
    lower = line.lower()
    if "read more:" in lower or "image:" in lower:
        return False
    if len(line) > 140:
        return False
    if len(line.split()) < 3:
        return False
    if line.endswith("."):
        return False
    return True

def extract_story_entries(body_content):
    entries = []
    current_title = ""
    for raw_line in (body_content or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        lower = line.lower()
        if "read more:" in lower:
            match = re.search(r"https?://\S+", line)
            if match:
                entries.append({
                    "title": current_title or "today's strongest 3D printing story",
                    "url": match.group(0).rstrip(").,]")
                })
            current_title = ""
            continue

        if "image:" in lower:
            continue

        if is_story_title_line(line) and not current_title:
            current_title = strip_leading_symbols(line)
    return entries

def find_story_entry(entries, predicate):
    for entry in entries:
        if predicate((entry.get("title") or "").lower()):
            return entry
    return None

def score_topic_interest(title):
    text = (title or "").lower()
    score = 0
    has_major_brand = any(brand in text for brand in MAJOR_RELEASE_BRANDS)
    has_release_term = any(term in text for term in MAJOR_RELEASE_TERMS)
    if has_major_brand and has_release_term:
        score += 8
    if "x2d" in text or "h2d" in text:
        score += 8
    if any(keyword in text for keyword in VIRAL_HINT_KEYWORDS):
        score += 5
    if any(keyword in text for keyword in RECYCLING_HINT_KEYWORDS):
        score += 3
    if "bambu" in text or "creality" in text:
        score += 1
    return score

def extract_pulse_date(pulse_title):
    match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", pulse_title or "")
    return match.group(1) if match else ""

def pick_template_for_date(date_key):
    key = date_key or "0000-00-00"
    index = sum(ord(ch) for ch in key) % len(DAILY_FOCUS_TEMPLATES)
    return DAILY_FOCUS_TEMPLATES[index]

def build_focus_sentence(body_content, pulse_title=""):
    pulse_date = extract_pulse_date(pulse_title)
    forced = FOCUS_OVERRIDE_BY_DATE.get(pulse_date)
    if forced:
        template = pick_template_for_date(pulse_date)
        text = template.format(
            topic=forced["topic"],
            reason="because it is the kind of viral, debate-driving story that sparks strong discussion",
            story_url=forced["story_url"],
            url=CANONICAL_SITE_URL
        )
        if forced.get("extra_url"):
            text += f" | Build files: {forced['extra_url']}"
        return text

    entries = extract_story_entries(body_content)
    x2d_entry = find_story_entry(
        entries,
        lambda title: "bambu" in title and "x2d" in title
    )
    if x2d_entry:
        return (
            "Today's conversation starter is Bambu Lab X2D serviceability: a community thread asks whether "
            "clearing a routine aux-extruder blockage should require such an involved teardown. "
            f"Join the discussion: {x2d_entry['url']} | Full pulse: {CANONICAL_SITE_URL}"
        )

    snapmaker_entry = find_story_entry(
        entries,
        lambda title: "snapmaker" in title and "u1" in title
    )
    bambu_launch_entry = find_story_entry(
        entries,
        lambda title: "bambu" in title and ("launch" in title or "new 3d printer" in title or "april 14" in title)
    )
    if snapmaker_entry and bambu_launch_entry:
        return (
            "Today's pulse focus is the Snapmaker U1 launch and Bambu Lab's new-printer reveal on April 14, "
            "because both stories are major desktop 3D printing moments for the community. "
            f"Snapmaker: {snapmaker_entry['url']} | Bambu: {bambu_launch_entry['url']} | "
            f"Full pulse: {CANONICAL_SITE_URL}"
        )

    if not entries:
        topic = "today's strongest 3D printing story"
        best_score = 0
        story_url = CANONICAL_SITE_URL
    else:
        best_entry = entries[0]
        best_title = best_entry["title"]
        best_score = score_topic_interest(best_title)
        for entry in entries[1:]:
            score = score_topic_interest(entry["title"])
            if score > best_score:
                best_entry = entry
                best_title = entry["title"]
                best_score = score
        topic = best_title
        story_url = best_entry.get("url") or CANONICAL_SITE_URL

    if best_score >= 5:
        reason = "because it is exactly the kind of viral, debate-driving update that pulls strong community attention"
    elif best_score >= 3:
        reason = "because closed-loop filament workflows are turning into a practical trend, not just a niche experiment"
    else:
        reason = "because it highlights where practical 3D printing innovation is moving next"

    template = pick_template_for_date(pulse_date)
    return template.format(topic=topic, reason=reason, story_url=story_url, url=CANONICAL_SITE_URL)

def parse_int_env(name, default):
    value = os.getenv(name, "").strip()
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default

def parse_float_env(name, default):
    value = os.getenv(name, "").strip()
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        return default

def parse_bool_env(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}

def parse_recipients(raw_value):
    recipients = []
    for part in (raw_value or "").split(","):
        candidate = part.strip()
        if candidate:
            recipients.append(candidate)
    return recipients

def load_dotenv_if_present(project_root):
    dotenv_path = os.path.join(project_root, ".env")
    if not os.path.exists(dotenv_path):
        return

    try:
        with open(dotenv_path, "r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if not key:
                    continue
                if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
                    value = value[1:-1]
                os.environ.setdefault(key, value)
    except OSError as exc:
        print(f"Warning: unable to read .env file: {exc}", file=sys.stderr)

def send_draft_to_gmail_if_configured(output_file, pulse_title, draft_content):
    if not parse_bool_env("PULSE_EMAIL_ENABLED", default=True):
        print("Gmail draft email skipped: PULSE_EMAIL_ENABLED is disabled.")
        return False

    gmail_user = os.getenv("PULSE_EMAIL_GMAIL_USER", "").strip()
    gmail_app_password = os.getenv("PULSE_EMAIL_GMAIL_APP_PASSWORD", "").strip()
    raw_recipients = os.getenv("PULSE_EMAIL_TO", "").strip() or gmail_user
    recipients = parse_recipients(raw_recipients)

    if not gmail_user or not gmail_app_password or not recipients:
        print(
            "Gmail draft email skipped: set PULSE_EMAIL_GMAIL_USER, "
            "PULSE_EMAIL_GMAIL_APP_PASSWORD, and optional PULSE_EMAIL_TO.",
            file=sys.stderr
        )
        return False

    pulse_date = extract_pulse_date(pulse_title) or "today"
    subject = os.getenv("PULSE_EMAIL_SUBJECT", "").strip() or f"Quality3Ds LinkedIn Draft - {pulse_date}"

    message = EmailMessage()
    message["From"] = gmail_user
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.set_content(
        "Your latest Quality3Ds LinkedIn draft is attached.\n\n"
        "This email was sent automatically after draft generation.\n\n"
        f"{draft_content}"
    )
    message.add_attachment(
        draft_content.encode("utf-8"),
        maintype="text",
        subtype="plain",
        filename=os.path.basename(output_file)
    )

    timeout_seconds = parse_float_env("PULSE_EMAIL_TIMEOUT_SECONDS", DEFAULT_EMAIL_TIMEOUT_SECONDS)
    max_retries = max(1, parse_int_env("PULSE_EMAIL_MAX_RETRIES", DEFAULT_EMAIL_MAX_RETRIES))
    retry_delay = max(1.0, parse_float_env("PULSE_EMAIL_RETRY_DELAY_SECONDS", DEFAULT_EMAIL_RETRY_DELAY_SECONDS))

    for attempt in range(1, max_retries + 1):
        try:
            with smtplib.SMTP_SSL(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT, timeout=timeout_seconds) as smtp:
                smtp.login(gmail_user, gmail_app_password)
                smtp.send_message(message)
            print(f"Gmail draft email sent to: {', '.join(recipients)}")
            return True
        except Exception as exc:
            if attempt >= max_retries:
                print(
                    f"Warning: failed to send Gmail draft email after {max_retries} attempts: {exc}",
                    file=sys.stderr
                )
                return False
            sleep_seconds = retry_delay * (2 ** (attempt - 1))
            print(
                f"Warning: Gmail send attempt {attempt}/{max_retries} failed ({exc}). "
                f"Retrying in {int(sleep_seconds)}s...",
                file=sys.stderr
            )
            time.sleep(sleep_seconds)
    return False

def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    load_dotenv_if_present(project_root)

    feed_path = 'feed.xml'
    if not os.path.exists(feed_path):
        print(f"Error: {feed_path} not found.")
        return

    try:
        tree = ET.parse(feed_path)
        root = tree.getroot()
        
        # Get the first item (latest news)
        channel = root.find('channel')
        latest_item = channel.find('item')
        
        if latest_item is None:
            print("No items found in the RSS feed.")
            return

        title = fix_mojibake(latest_item.find('title').text or "")
        link = normalize_quality3ds_link(fix_mojibake(latest_item.find('link').text or ""))
        description_html = fix_mojibake(latest_item.find('description').text or "")
        
        # Format the content
        body_content = clean_html_for_markdown(description_html)
        focus_sentence = build_focus_sentence(body_content, title)
        
        draft_content = f"""# {title}

{body_content}

---
*Originally published at: {link}*
{focus_sentence}"""
        
        output_file = os.path.join(project_root, 'LINKEDIN_DRAFT.txt')
        with open(output_file, 'w', encoding='utf-8-sig') as f:
            f.write(draft_content)
            
        print(f"Draft created successfully: {output_file}")
        print("Content is ready to be copied into your LinkedIn Newsletter.")
        send_draft_to_gmail_if_configured(output_file, title, draft_content)

    except Exception as e:
        print(f"Error parsing feed: {e}")

if __name__ == "__main__":
    main()
