import os
import glob
import datetime
import markdown
import re
from xml.etree.ElementTree import Element, SubElement, ElementTree

# Configuration
REPO_URL = "https://github.com/Bennyco86/3DprintingPulse"
SITE_URL = "https://quality3ds.godaddysites.com"
FEED_FILE = "feed.xml"
README_FILE = "README.md"
MAX_PULSES = 10
TITLE = "Quality3Ds Daily Pulse"
DESCRIPTION = "Curated daily news for 3D printing enthusiasts."
PLACEHOLDER_LINES = {
    '?? Headline here',
    '\U0001F4F0 Headline here',
    'Headline here',
    'Hook sentence.',
    'Concrete detail sentence.',
    'Read more ? https://example.com',
    '(Repeat per story; separate stories with one blank line.)'
}

# Pulse #1 was likely Jan 7 or Jan 8 based on Jan 14 being #7.
# Let's set the reference: Jan 14, 2026 is Pulse #7.
REFERENCE_DATE = datetime.date(2026, 1, 14)
REFERENCE_NUMBER = 7

def calculate_pulse_number(date_obj):
    delta = (date_obj - REFERENCE_DATE).days
    return REFERENCE_NUMBER + delta

def parse_date_from_path(file_path):
    date_str = os.path.dirname(file_path).split(os.sep)[-1]
    try:
        year, month, day = map(int, date_str.split('-'))
        return date_str, datetime.date(year, month, day)
    except ValueError:
        return None, None

def extract_markdown_body(content):
    lines = content.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.lstrip('\ufeff')
        trimmed = line.strip()
        if trimmed.startswith('# Quality3Ds Daily'):
            continue
        if trimmed.startswith('## Stories'):
            continue
        if trimmed.startswith('TODO:'):
            continue
        if trimmed.startswith('Template'):
            continue
        if trimmed in PLACEHOLDER_LINES:
            continue
        cleaned_lines.append(line)
    return '\n'.join(cleaned_lines).strip()

def load_markdown_body(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().lstrip('\ufeff')
    return extract_markdown_body(content)

def normalize_for_compare(markdown_body):
    return '\n'.join([line.strip() for line in markdown_body.splitlines() if line.strip()])

def normalize_markdown(markdown_body):
    return re.sub(r"^\?\?\s+", "\U0001F4F0 ", markdown_body, flags=re.M)

def build_latest_section(pulse_title, markdown_body):
    cleaned_body = normalize_markdown(markdown_body).strip()
    if not cleaned_body:
        cleaned_body = "(No stories yet.)"
    return "\n".join([
        "## Latest Pulse",
        "<!-- PULSE:START -->",
        f"### {pulse_title}",
        "",
        cleaned_body,
        "<!-- PULSE:END -->"
    ])

def update_root_readme(pulse_title, markdown_body):
    if not os.path.exists(README_FILE):
        return

    with open(README_FILE, 'r', encoding='utf-8') as f:
        readme = f.read()

    latest_section = build_latest_section(pulse_title, markdown_body)
    pattern = re.compile(r"## Latest Pulse\s*<!-- PULSE:START -->.*?<!-- PULSE:END -->", re.S)
    if pattern.search(readme):
        updated = pattern.sub(latest_section, readme)
    else:
        parts = readme.split('\n', 1)
        if len(parts) == 2:
            updated = parts[0] + "\n\n" + latest_section + "\n\n" + parts[1].lstrip()
        else:
            updated = readme + "\n\n" + latest_section

    with open(README_FILE, 'w', encoding='utf-8') as f:
        f.write(updated.rstrip() + "\n")

def generate_rss():
    root = Element('rss')
    root.set('version', '2.0')
    channel = SubElement(root, 'channel')

    SubElement(channel, 'title').text = TITLE
    SubElement(channel, 'link').text = SITE_URL
    SubElement(channel, 'description').text = DESCRIPTION

    # Find all daily folders (YYYY-MM-DD)
    search_path = os.path.join('.', '20??-??-??', 'README.md')
    files = glob.glob(search_path)
    files.sort(reverse=True) # Newest first
    files = files[:MAX_PULSES]

    dated_files = []
    for file_path in files:
        date_str, date_obj = parse_date_from_path(file_path)
        if not date_obj:
            continue
        dated_files.append((file_path, date_str, date_obj))

    if not dated_files:
        raise SystemExit("No daily README files found (expected ./YYYY-MM-DD/README.md).")

    latest_body = load_markdown_body(dated_files[0][0])
    if not latest_body:
        raise SystemExit(f"Latest daily README has no stories: {dated_files[0][0]}")

    if len(dated_files) > 1:
        previous_body = load_markdown_body(dated_files[1][0])
        if normalize_for_compare(latest_body) == normalize_for_compare(previous_body):
            raise SystemExit("Latest daily README matches the previous day's stories. Update it before publishing.")

    last_build_date = datetime.datetime.combine(dated_files[0][2], datetime.time(hour=12))
    SubElement(channel, 'lastBuildDate').text = last_build_date.strftime("%a, %d %b %Y %H:%M:%S GMT")

    latest_payload = None

    for idx, (file_path, date_str, current_date) in enumerate(dated_files):

        pulse_num = calculate_pulse_number(current_date)
        
        markdown_body = load_markdown_body(file_path)

        # Convert to HTML
        html_body = markdown.markdown(markdown_body)
        
        # Create ONE RSS Item for the whole day
        item = SubElement(channel, 'item')
        
        # Title: "3D PRINTING PULSE #7 - 2026-01-14"
        post_title = f"3D PRINTING PULSE #{pulse_num} - {date_str}"
        SubElement(item, 'title').text = post_title
        
        # Link: To the website (or GitHub if no site page exists)
        SubElement(item, 'link').text = SITE_URL
        
        # Description: The Full HTML Content
        SubElement(item, 'description').text = html_body
        
        # Date
        SubElement(item, 'pubDate').text = current_date.strftime("%a, %d %b %Y 12:00:00 GMT")
        SubElement(item, 'guid').text = f"pulse-{pulse_num}-{date_str}"

        if idx == 0:
            latest_payload = (post_title, markdown_body)

    # Write to file with explicit encoding; avoid charref-mojibake in emoji
    ElementTree(root).write(FEED_FILE, encoding='utf-8', xml_declaration=True)

    if latest_payload:
        update_root_readme(*latest_payload)
    
    print(f"Generated {FEED_FILE} with {len(dated_files)} daily pulses.")

if __name__ == "__main__":
    generate_rss()

