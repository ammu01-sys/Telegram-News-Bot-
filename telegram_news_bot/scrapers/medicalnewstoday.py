import requests
from bs4 import BeautifulSoup
from datetime import datetime
from ..utils.logger import get_logger
from ..services.cleaner import extract_published_at

log = get_logger(__name__)

SOURCE_NAME = "Medical News Today"
BASE_URL = "https://www.medicalnewstoday.com/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def scrape() -> list[dict]:
    articles = []
    seen_urls = set()

    try:
        resp = requests.get(BASE_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        log.error(f"Medical News Today homepage request failed: {e}")
        return []

    try:
        soup = BeautifulSoup(resp.text, "lxml")
        links = soup.select("a[href*='/articles/']")
        for link in links:
            href = link.get("href", "")
            if href.startswith("//"):
                href = "https:" + href
            elif href.startswith("/"):
                href = "https://www.medicalnewstoday.com" + href
            elif not href.startswith("http"):
                continue

            if href in seen_urls:
                continue
            seen_urls.add(href)

            skip_patterns = ["#", "example.com", "/category/", "/page/"]
            if any(p in href for p in skip_patterns):
                continue

            article = _scrape_article(href)
            if article:
                articles.append(article)
    except Exception as e:
        log.error(f"Medical News Today parse error: {e}")

    log.info(f"Medical News Today scraped {len(articles)} articles")
    return articles


def _scrape_article(url: str) -> dict | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        log.error(f"Medical News Today article request failed {url}: {e}")
        return None

    try:
        soup = BeautifulSoup(resp.text, "lxml")

        og_title = soup.find("meta", property="og:title")
        title = og_title.get("content") if og_title else None
        if not title:
            h1 = soup.find("h1")
            title = h1.get_text(strip=True) if h1 else "No title"

        content_parts = []
        for sel in ["article p", "div.article-body p", ".content p", "main p"]:
            paragraphs = soup.select(sel)
            if paragraphs:
                for p in paragraphs[:20]:
                    text = p.get_text(strip=True)
                    if text and len(text) > 20:
                        content_parts.append(text)
                if content_parts:
                    break

        content = " ".join(content_parts)
        if len(content) < 100:
            return None

        words = content.split()
        if len(words) > 600:
            content = " ".join(words[:600])

        published_at = extract_published_at(soup)

        return {
            "title": title,
            "url": url,
            "content": content,
            "source_name": SOURCE_NAME,
            "published_at": published_at,
            "scraped_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        log.error(f"Medical News Today article parse error {url}: {e}")
        return None
