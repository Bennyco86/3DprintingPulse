import datetime
import email.utils
import glob
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

SOURCES_FILE = "sources.json"
MIN_STORIES = 4
MAX_STORIES = 8
MAX_ITEM_AGE_HOURS = 36
REQUIRED_CATEGORIES = ["medical", "aerospace", "construction"]
PREFERRED_CATEGORIES = ["recycling"]
BLOCKLIST_TITLE_PHRASES = ["news briefs"]
NON_ENGLISH_HINT_WORDS = {
    "ejercito", "explora", "posibilidad", "usar", "alimentos", "impresos",
    "solucion", "militar", "investigadores", "tecnologia", "impresion",
    "empresa", "desarrolla", "presenta", "anuncia", "fabricacion"
}
NON_ENGLISH_URL_PATH_HINTS = (
    "/es/", "/de/", "/fr/", "/it/", "/pt/", "/jp/", "/kr/", "/cn/"
)

CATEGORY_KEYWORDS = {
    "medical": [
        "medical", "hospital", "clinic", "implant", "prosthetic", "prosthesis",
        "bioprint", "bioprinting", "surgery", "surgical", "tissue", "cancer",
        "lung", "orthopedic", "radiation"
    ],
    "aerospace": [
        "rocket", "space", "aerospace", "nasa", "launch", "satellite",
        "propulsion", "engine", "rutherford"
    ],
    "construction": [
        "construction", "building", "house", "housing", "home", "bridge",
        "concrete", "cement", "infrastructure", "printed neighborhood"
    ],
    "recycling": [
        "closed-loop", "closed loop", "recycle", "recycled", "recycling",
        "regrind", "grind", "shredder", "shredding", "pellet", "pelletize",
        "pelletizer", "filament recycling", "filament recycler",
        "filament maker", "filament manufacturing", "filament extruder",
        "pellet extruder", "waste plastic", "plastic waste"
    ],
    "printers": [
        "printer", "fdm", "resin", "sla", "sls", "slm", "metal",
        "build volume", "nozzle", "filament", "bambu", "creality",
        "prusa", "elegoo", "sovol", "ultimaker", "formlabs"
    ],
    "scanners": [
        "scanner", "scan", "metrology", "lidar"
    ],
    "software": [
        "software", "slicer", "ai", "automation", "simulation", "workflow",
        "firmware", "cad", "cam"
    ]
}

CATEGORY_EMOJI = {
    "medical": "\U0001F9BA",
    "aerospace": "\U0001F680",
    "construction": "\U0001F3E0",
    "recycling": "\u267B\ufe0f",
    "printers": "\U0001F5A8",
    "scanners": "\U0001F4F7",
    "software": "\U0001F4BB",
    "general": "\U0001F4F0"
}

DEFAULT_SOURCES = [
    {"name": "3D Printing Industry", "url": "https://3dprintingindustry.com/feed/"},
    {"name": "3DPrint.com", "url": "https://3dprint.com/feed/"},
    {"name": "VoxelMatters", "url": "https://www.voxelmatters.com/feed/"},
    {"name": "Fabbaloo", "url": "https://www.fabbaloo.com/feed"},
    {"name": "All3DP", "url": "https://all3dp.com/feed/"},
    {"name": "Bambu Lab", "url": "https://blog.bambulab.com/feed/"}
]

USER_AGENT = "Quality3DsPulseBot/1.0 (+https://quality3ds.godaddysites.com)"
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "mc_cid", "mc_eid"
}
DEBUG_ENCODING = os.getenv("PULSE_DEBUG_ENCODING") == "1"
MOJIBAKE_MARKERS = (
    "\u00c3",               # A-tilde fragment
    "\u00c2",               # A-circumflex fragment
    "\u00e2\u20ac",         # "a-euro" prefix from mojibake punctuation
    "\u00f0\u0178",         # emoji lead (mojibake)
    "\u00ef\u00bf\u00bd"    # replacement char (mojibake)
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


def mojibake_score(text):
    return sum(text.count(marker) for marker in MOJIBAKE_MARKERS)


def looks_mojibake(text):
    if not text:
        return False
    return mojibake_score(text) > 0


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
    if mojibake_score(repaired) >= mojibake_score(chunk):
        return chunk
    return repaired


def repair_mojibake_once(text):
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


def fix_mojibake_line(text):
    if not text or not looks_mojibake(text):
        return text

    fixed = text
    for _ in range(2):
        candidate = repair_mojibake_once(fixed)
        if candidate == fixed:
            break
        if mojibake_score(candidate) >= mojibake_score(fixed):
            break
        fixed = candidate
        if not looks_mojibake(fixed):
            break
    return fixed


def fix_mojibake(text, context=""):
    if not text or not looks_mojibake(text):
        return text

    original = text
    if "\n" in text or "\r" in text:
        fixed = "".join(fix_mojibake_line(line) for line in text.splitlines(keepends=True))
    else:
        fixed = fix_mojibake_line(text)

    if fixed != original and DEBUG_ENCODING:
        print(f"[encoding] repaired {context}: {original} -> {fixed}", file=sys.stderr)
    return fixed


def load_sources(project_root):
    path = os.path.join(project_root, SOURCES_FILE)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, list) or not data:
            raise SystemExit("sources.json must be a non-empty list of sources.")
        return data
    return DEFAULT_SOURCES


def strip_html(value):
    text = html.unescape(value or "")
    text = fix_mojibake(text, "strip_html")
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def split_sentences(text):
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [part.strip() for part in parts if part.strip()]

def filter_summary_sentences(sentences):
    filtered = []
    for sentence in sentences:
        words = sentence.split()
        if len(words) < 3 and len(sentence) < 25:
            continue
        filtered.append(sentence)
    return filtered


def clamp_sentence(text, max_len=220):
    if len(text) <= max_len:
        return text
    truncated = text[:max_len - 3].rsplit(" ", 1)[0]
    return (truncated or text[:max_len - 3]) + "..."


def parse_date(value):
    if not value:
        return None
    try:
        parsed = email.utils.parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=datetime.timezone.utc)
        return parsed.astimezone(datetime.timezone.utc)
    except (TypeError, ValueError):
        pass
    try:
        parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=datetime.timezone.utc)
        return parsed.astimezone(datetime.timezone.utc)
    except ValueError:
        return None


def format_date(value):
    if not value:
        return ""
    return value.astimezone(datetime.timezone.utc).strftime("%b %d, %Y")


def get_text(element, *paths):
    for path in paths:
        text = element.findtext(path)
        if text:
            return text.strip()
    return ""


def extract_atom_link(entry):
    for link in entry.findall("{*}link"):
        href = link.attrib.get("href")
        rel = link.attrib.get("rel", "alternate")
        if rel == "alternate" and href:
            return href
    return get_text(entry, "{*}link")

def extract_image_from_element(element):
    for tag in ("thumbnail", "content"):
        for node in element.findall(f".//{{*}}{tag}"):
            url = node.attrib.get("url") or node.attrib.get("href")
            if not url:
                continue
            media_type = (node.attrib.get("type") or node.attrib.get("medium") or "").lower()
            if not media_type or "image" in media_type:
                return url

    for node in element.findall(".//{*}enclosure"):
        url = node.attrib.get("url") or node.attrib.get("href")
        if not url:
            continue
        media_type = (node.attrib.get("type") or "").lower()
        if not media_type or media_type.startswith("image/"):
            return url

    image_url = get_text(element, "image/url", "{*}image/{*}url")
    if image_url:
        return image_url

    for link in element.findall("{*}link"):
        href = link.attrib.get("href")
        rel = link.attrib.get("rel", "")
        media_type = (link.attrib.get("type") or "").lower()
        if href and rel == "enclosure" and (not media_type or media_type.startswith("image/")):
            return href

    return ""


def fetch_feed(source):
    url = source.get("url", "")
    if not url:
        return []
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            data = response.read()
    except Exception as exc:
        print(f"Warning: failed to fetch {url}: {exc}", file=sys.stderr)
        return []

    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        print(f"Warning: failed to parse {url}: {exc}", file=sys.stderr)
        return []

    items = []
    for item in root.findall(".//item"):
        title = fix_mojibake(get_text(item, "title", "{*}title"), "rss_title")
        link = get_text(item, "link", "{*}link")
        summary = fix_mojibake(get_text(item, "description", "{*}description"), "rss_summary")
        published = get_text(item, "pubDate", "{*}pubDate", "dc:date", "{*}date")
        image = extract_image_from_element(item)
        items.append({
            "title": title,
            "url": link,
            "summary": summary,
            "published": parse_date(published),
            "image": image,
            "source": source.get("name") or urllib.parse.urlparse(url).hostname or "Source"
        })

    if items:
        return items

    for entry in root.findall(".//{*}entry"):
        title = fix_mojibake(get_text(entry, "{*}title"), "atom_title")
        link = extract_atom_link(entry)
        summary = fix_mojibake(get_text(entry, "{*}summary", "{*}content"), "atom_summary")
        published = get_text(entry, "{*}published", "{*}updated")
        image = extract_image_from_element(entry)
        items.append({
            "title": title,
            "url": link,
            "summary": summary,
            "published": parse_date(published),
            "image": image,
            "source": source.get("name") or urllib.parse.urlparse(url).hostname or "Source"
        })
    return items


def classify_item(item):
    text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                return category
    return "general"


def normalize_url(url):
    if not url:
        return ""
    try:
        parsed = urllib.parse.urlsplit(url)
    except ValueError:
        return url

    if not parsed.scheme or not parsed.netloc:
        return url

    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    cleaned_query = [(k, v) for k, v in query if k not in TRACKING_PARAMS]
    cleaned_query.sort()

    cleaned = urllib.parse.urlunsplit((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        parsed.path.rstrip("/"),
        urllib.parse.urlencode(cleaned_query, doseq=True),
        ""
    ))
    return cleaned


def is_valid_story_url(url):
    if not url:
        return False
    try:
        parsed = urllib.parse.urlsplit(url)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def normalize_title_for_dedupe(title):
    if not title:
        return ""
    text = strip_html(title).lower()
    text = re.sub(r"\s+", " ", text).strip()
    dash_parts = re.split(r"\s[-|:]\s", text)
    if len(dash_parts) > 1:
        tail = dash_parts[-1].strip()
        if 1 <= len(tail) <= 40 and len(tail.split()) <= 5:
            text = " - ".join(dash_parts[:-1]).strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\b(the|a|an)\b", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def is_probably_non_english(title, summary, url=""):
    text = f"{title or ''} {summary or ''}".lower()
    words = set(re.findall(r"[a-zA-Z\u00c0-\u017f]+", text))
    hint_hits = sum(1 for word in NON_ENGLISH_HINT_WORDS if word in words)

    has_diacritics = bool(re.search(r"[\u00c0-\u017f]", text))
    url_lower = (url or "").lower()
    has_language_path = any(token in url_lower for token in NON_ENGLISH_URL_PATH_HINTS)

    if has_language_path and hint_hits >= 1:
        return True
    if hint_hits >= 2:
        return True
    if has_diacritics and hint_hits >= 1:
        return True
    return False


def source_preference_score(source_name):
    source = (source_name or "").lower()
    if "google news" in source:
        return 0
    return 1


def load_seen_urls(project_root, exclude_date=None):
    seen = set()
    paths = glob.glob(os.path.join(project_root, "20??-??-??", "README.md"))
    paths.sort(reverse=True)
    skip_path = None
    if exclude_date:
        skip_path = os.path.normcase(os.path.join(project_root, exclude_date, "README.md"))
    for path in paths:
        if skip_path and os.path.normcase(path) == skip_path:
            continue
        try:
            with open(path, "r", encoding="utf-8") as handle:
                for line in handle:
                    if "Read more" not in line:
                        continue
                    match = re.search(r"https?://\S+", line)
                    if match:
                        url = match.group(0).rstrip(").,]")
                        url = normalize_url(url)
                        if "example.com" not in url:
                            seen.add(url)
        except OSError:
            continue
    return seen


def select_stories(items, seen_urls):
    now = datetime.datetime.now(datetime.timezone.utc)
    cutoff = now - datetime.timedelta(hours=MAX_ITEM_AGE_HOURS)
    candidates = []
    for item in items:
        url = normalize_url(item.get("url", "").strip())
        title = item.get("title", "").strip()
        title_lower = title.lower()
        published = item.get("published")
        if not is_valid_story_url(url) or not title:
            continue
        if any(phrase in title_lower for phrase in BLOCKLIST_TITLE_PHRASES):
            continue
        # Google News links are aggregator redirects; keep direct source links only.
        if source_preference_score(item.get("source", "")) == 0:
            continue
        if is_probably_non_english(title, item.get("summary", ""), url):
            continue
        if url in seen_urls:
            continue
        if not published or published < cutoff:
            continue
        item["summary"] = strip_html(item.get("summary", ""))
        item["category"] = classify_item(item)
        item["url"] = url
        item["title_signature"] = normalize_title_for_dedupe(title)
        item["source_score"] = source_preference_score(item.get("source", ""))
        candidates.append(item)

    if not candidates:
        return []

    recent = list(candidates)
    recent.sort(key=lambda item: (item.get("source_score", 0), item.get("published")), reverse=True)

    selected = []
    used_urls = set()
    used_signatures = set()
    for category in REQUIRED_CATEGORIES:
        for item in recent:
            if (
                item["category"] == category
                and item["url"] not in used_urls
                and item.get("title_signature", "") not in used_signatures
            ):
                selected.append(item)
                used_urls.add(item["url"])
                if item.get("title_signature"):
                    used_signatures.add(item["title_signature"])
                break

    for category in PREFERRED_CATEGORIES:
        for item in recent:
            if (
                item["category"] == category
                and item["url"] not in used_urls
                and item.get("title_signature", "") not in used_signatures
            ):
                selected.append(item)
                used_urls.add(item["url"])
                if item.get("title_signature"):
                    used_signatures.add(item["title_signature"])
                break

    for item in recent:
        if len(selected) >= MAX_STORIES:
            break
        if item["url"] in used_urls:
            continue
        if item.get("title_signature", "") in used_signatures:
            continue
        selected.append(item)
        used_urls.add(item["url"])
        if item.get("title_signature"):
            used_signatures.add(item["title_signature"])

    return selected


def build_story_lines(item):
    title = item.get("title", "").strip() or "Untitled story"
    summary = item.get("summary", "")
    sentences = split_sentences(summary)
    filtered = filter_summary_sentences(sentences)
    if filtered:
        sentences = filtered
    source = item.get("source", "Source")
    published = format_date(item.get("published"))
    image = item.get("image", "")
    if sentences:
        hook = clamp_sentence(sentences[0])
        detail = clamp_sentence(sentences[1]) if len(sentences) > 1 else ""
    else:
        hook = ""
        detail = ""

    if not hook:
        hook = f"Coverage from {source} highlights this update."
    if not detail or detail == hook:
        detail = f"Reported by {source}{' on ' + published if published else ''}."
    else:
        detail_lower = detail.lower()
        if "reported by" not in detail_lower and source.lower() not in detail_lower:
            tag = f"reported by {source}{' on ' + published if published else ''}"
            detail = detail.rstrip().rstrip(".!?")
            detail = f"{detail}, {tag}."

    emoji = CATEGORY_EMOJI.get(item.get("category"), CATEGORY_EMOJI["general"])

    lines = [
        f"{emoji} {title}",
        hook,
        detail,
    ]
    if image:
        lines.append(f"Image ? {image}")
    lines.extend([
        f"Read more ? {item.get('url')}",
        ""
    ])
    return lines


def has_real_content(text):
    if not text:
        return False
    if "TODO:" in text:
        return False
    if "Template (delete this block once filled):" in text:
        return False
    if "Headline here" in text:
        return False
    return True


def main():
    force = "--force" in sys.argv
    project_root = os.path.dirname(os.path.abspath(__file__))
    date_stamp = datetime.datetime.now().strftime("%Y-%m-%d")
    out_dir = os.path.join(project_root, date_stamp)
    out_file = os.path.join(out_dir, "README.md")

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    if os.path.exists(out_file):
        with open(out_file, "r", encoding="utf-8") as handle:
            existing = handle.read()
        if has_real_content(existing) and not force:
            print(f"Daily README already populated: {out_file}")
            return 0

    sources = load_sources(project_root)
    items = []
    for source in sources:
        items.extend(fetch_feed(source))

    if not items:
        raise SystemExit("No feed items found. Check sources.json and network access.")

    seen_urls = load_seen_urls(project_root, exclude_date=date_stamp if force else None)
    selected = select_stories(items, seen_urls)
    if len(selected) < MIN_STORIES:
        raise SystemExit(
            f"Only found {len(selected)} fresh unique stories in the last {MAX_ITEM_AGE_HOURS}h. "
            "Add sources or fill manually."
        )

    lines = [
        f"# Quality3Ds Daily 3D Printing News - {date_stamp}",
        "",
        "## Stories",
        ""
    ]
    for item in selected:
        lines.extend(build_story_lines(item))

    with open(out_file, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines).rstrip() + "\n")

    print(f"Wrote {out_file} with {len(selected)} stories.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
