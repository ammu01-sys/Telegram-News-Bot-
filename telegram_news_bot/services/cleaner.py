import re
from datetime import datetime
from bs4 import BeautifulSoup

# Tags to remove entirely (including children) before extracting text.
# This prevents image alt text, captions, video descriptions, etc.
# from polluting article content.
_STRIP_TAGS = [
    "img", "figure", "figcaption", "picture",
    "video", "source", "audio", "iframe",
    "svg", "canvas", "embed", "object",
    "nav", "footer", "header", "aside",
    "script", "style", "noscript",
]


def strip_html(text: str) -> str:
    soup = BeautifulSoup(text, "lxml")

    # Decompose all visual/media/navigation elements
    for tag_name in _STRIP_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    return soup.get_text(separator=" ")


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_article(article: dict) -> dict:
    result = dict(article)
    if "title" in result and result["title"]:
        result["title"] = normalize_text(strip_html(result["title"]))
    if "content" in result and result["content"]:
        result["content"] = normalize_text(strip_html(result["content"]))
    return result


def extract_published_at(soup: BeautifulSoup) -> str | None:
    selectors = [
        ("meta", {"property": "article:published_time"}, "content"),
        ("meta", {"name": "pubdate"}, "content"),
        ("meta", {"name": "dc.date"}, "content"),
        ("meta", {"property": "article:modified_time"}, "content"),
        ("time", {"datetime": True}, "datetime"),
    ]
    for tag, attrs, attr_name in selectors:
        elem = soup.find(tag, attrs)
        if elem:
            val = elem.get(attr_name)
            if val:
                try:
                    val = val.strip().replace("Z", "+00:00")
                    dt = datetime.fromisoformat(val)
                    return dt.isoformat()
                except (ValueError, TypeError):
                    continue

    # JSON-LD fallback
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            import json
            data = json.loads(script.string)
            for key in ("datePublished", "dateCreated"):
                val = data.get(key) or (data.get("datePublished"))
                if val:
                    val = val.strip().replace("Z", "+00:00")
                    return datetime.fromisoformat(val).isoformat()
        except Exception:
            continue

    return None
