import requests
from bs4 import BeautifulSoup
from datetime import datetime
from ..utils.logger import get_logger
from ..services.cleaner import extract_published_at

log = get_logger(__name__)

BASE_URL = "https://cointelegraph.com"

def fetch_content(url: str, headers: dict) -> tuple[str, BeautifulSoup | None]:
    try:
        res = requests.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(res.text, "lxml")
        # Try multiple content selectors
        selectors = [
            "div.post-content p",
            "div[class*='post-content'] p",
            "article p",
            "main p",
            ".article-content p",
            "div[class*='article'] p"
        ]
        for selector in selectors:
            paragraphs = soup.select(selector)
            if paragraphs:
                text = " ".join(p.get_text(strip=True) for p in paragraphs[:10])
                if len(text) > 100:
                    return text[:2000], soup
        # Last fallback: all p tags
        all_p = soup.find_all("p")
        return " ".join(p.get_text(strip=True) for p in all_p[:10])[:2000], soup
    except Exception as e:
        log.error(f"Content fetch failed for {url}: {e}")
        return "", None


def scrape() -> list[dict]:
    articles = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    seen_urls = set()

    try:
        res = requests.get(BASE_URL, headers=headers, timeout=30)
        soup = BeautifulSoup(res.text, "lxml")

        # Try multiple link selectors
        link_selectors = [
            "a[href*='/news/']",
            "article a[href]",
            "h2 a[href]",
            "h3 a[href]",
            ".post-card a[href]",
            "div[class*='post'] a[href]"
        ]

        links = []
        for selector in link_selectors:
            found = soup.select(selector)
            if found:
                links.extend(found)

        log.info(f"CoinTelegraph: found {len(links)} raw links")

        for tag in links:
            href = tag.get("href", "")
            if not href:
                continue

            # Build full URL
            if href.startswith("/"):
                href = BASE_URL + href
            if not href.startswith("http"):
                continue

            # Must be a news URL
            if "/news/" not in href:
                continue

            # Skip invalid patterns
            skip_patterns = ["/tag/", "/author/", "/category/", "/page/", "#", "example.com"]
            if any(p in href for p in skip_patterns):
                continue

            # Deduplicate
            if href in seen_urls:
                continue
            seen_urls.add(href)

            # Get title
            title = tag.get_text(strip=True)
            if not title or len(title) < 10:
                # Try parent elements
                parent = tag.find_parent(["h1", "h2", "h3", "h4"])
                if parent:
                    title = parent.get_text(strip=True)
            if not title or len(title) < 10:
                continue

            # Fetch article content and extract date from same response
            content, article_soup = fetch_content(href, headers)
            if len(content) < 50:
                continue

            published_at = extract_published_at(article_soup) if article_soup else None

            articles.append({
                "title": title,
                "url": href,
                "content": content,
                "source_name": "CoinTelegraph",
                "published_at": published_at,
                "scraped_at": datetime.utcnow().isoformat()
            })

        log.info(f"CoinTelegraph scraped {len(articles)} articles")

    except Exception as e:
        log.error(f"CoinTelegraph scrape failed: {e}")

    return articles


if __name__ == "__main__":
    results = scrape()
    for r in results[:3]:
        print(r['title'], "→", r['url'])
