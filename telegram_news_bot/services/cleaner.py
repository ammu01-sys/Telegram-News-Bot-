import re
from datetime import datetime
from bs4 import BeautifulSoup


def strip_html(text: str) -> str:
    soup = BeautifulSoup(text, "lxml")
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
