import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from ..utils.logger import get_logger

log = get_logger(__name__)

SOURCE_NAME = "CNBC"
RSS_URL = "https://www.cnbc.com/id/100003114/device/rss/rss.html"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}


def scrape() -> list[dict]:
    articles = []

    try:
        feed = feedparser.parse(RSS_URL)
    except Exception as e:
        log.error(f"CNBC RSS parse failed: {e}")
        return []

    if not feed.entries:
        log.warning("CNBC RSS feed returned no entries")
        return []

    log.info(f"CNBC RSS: {len(feed.entries)} entries found")

    for entry in feed.entries:
        title = entry.get("title", "").strip()
        url = entry.get("link", "").strip()
        if not title or not url:
            continue

        # Skip non-article links
        skip_patterns = ["/video/", "/live/", "/watch/", "/pro/"]
        if any(p in url for p in skip_patterns):
            continue

        # Extract published date from feed entry
        published_at = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                published_at = datetime(*entry.published_parsed[:6]).isoformat()
            except Exception:
                pass

        # Try to fetch full article content
        content = _fetch_article_content(url)
        if not content:
            # Fallback to feed summary
            content = entry.get("summary", "") or ""
            content = BeautifulSoup(content, "html.parser").get_text(strip=True)

        if len(content) < 100:
            continue

        # Cap content at ~600 words
        words = content.split()
        if len(words) > 600:
            content = " ".join(words[:600])

        articles.append({
            "title": title,
            "url": url,
            "content": content,
            "source_name": SOURCE_NAME,
            "published_at": published_at,
            "scraped_at": datetime.utcnow().isoformat(),
        })

    log.info(f"CNBC scraped {len(articles)} articles")
    return articles


def _fetch_article_content(url: str) -> str:
    """Fetch and extract article body from CNBC page."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            return ""
    except Exception as e:
        log.debug(f"CNBC article fetch failed {url}: {e}")
        return ""

    try:
        soup = BeautifulSoup(resp.text, "lxml")

        # Remove images, figures, captions, and media elements
        for tag in soup.find_all(["img", "figure", "figcaption", "picture", "video", "svg"]):
            tag.decompose()

        content_parts = []
        for sel in ["div.ArticleBody-articleBody p", "div.group p", "article p"]:
            paragraphs = soup.select(sel)
            if paragraphs:
                for p in paragraphs[:20]:
                    # Skip paragraphs inside captions or media containers
                    if p.find_parent(["figure", "figcaption", "picture"]):
                        continue
                    text = p.get_text(strip=True)
                    if text and len(text) > 20:
                        content_parts.append(text)
                if content_parts:
                    break
        return " ".join(content_parts)
    except Exception as e:
        log.debug(f"CNBC article parse error {url}: {e}")
        return ""
