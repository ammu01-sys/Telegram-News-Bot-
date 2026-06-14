import re
from datetime import datetime, timezone
from bs4 import BeautifulSoup


def clean_article(article: dict) -> dict:
    """
    Input:  raw scraper dict {title, url, content, timestamp, source_name}
    Output: cleaned dict with published_at (datetime) added
    """
    article["title"]        = _clean_text(article.get("title", ""))
    article["content"]      = _clean_text(article.get("content", ""))
    article["published_at"] = _parse_timestamp(article.get("timestamp", ""))
    return article


def _clean_text(text: str) -> str:
    # Strip HTML tags if any slipped through
    text = BeautifulSoup(text, "lxml").get_text(separator=" ")
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _parse_timestamp(raw: str) -> str | None:
    """Normalize any ISO-8601 string to UTC ISO format."""
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return None
