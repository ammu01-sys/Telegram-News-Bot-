import requests
from bs4 import BeautifulSoup
from datetime import datetime
from ..utils.logger import get_logger
from ..services.cleaner import extract_published_at

logger = get_logger(__name__)

SOURCE_NAME = "Blockworks"
BASE_URL = "https://blockworks.co/news"
# Headers include a realistic User-Agent and other typical browser headers
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.google.com/",
}


def scrape() -> list[dict]:
    articles = []
    seen_urls = set()

    try:
        resp = requests.get(BASE_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        # Log the error and return an empty list – the rest of the pipeline can continue
        logger.error(f"Blockworks homepage request failed: {e}")
        return []

    try:
        soup = BeautifulSoup(resp.text, "lxml")
        links = soup.select("a[href*='/news/']")
        for link in links:
            href = link.get("href", "")
            if not href.startswith("http"):
                full_url = "https://blockworks.co" + href if href.startswith("/") else "https://blockworks.co/" + href
            else:
                full_url = href
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            # Skip tag, author, category, page URLs and anchors
            skip_patterns = ['example.com', '/tag/', '/author/', '/category/', '/page/', '#']
            if any(p in full_url for p in skip_patterns):
                continue

            article = _scrape_article(full_url)
            if article:
                articles.append(article)
    except Exception as e:
        logger.error(f"Blockworks parse error: {e}")

    logger.info(f"Blockworks scraped {len(articles)} articles")
    return articles


def _scrape_article(url: str) -> dict | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"Blockworks article request failed {url}: {e}")
        return None

    try:
        soup = BeautifulSoup(resp.text, "lxml")

        og_title = soup.find("meta", property="og:title")
        title = og_title.get("content") if og_title else None
        if not title:
            h1 = soup.find("h1")
            title = h1.get_text(strip=True) if h1 else "No title"

        content_parts = []
        article_tag = soup.find("article")
        if article_tag:
            for p in article_tag.find_all("p"):
                text = p.get_text(strip=True)
                if text:
                    content_parts.append(text)

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
        logger.error(f"Blockworks article parse error {url}: {e}")
        return None
