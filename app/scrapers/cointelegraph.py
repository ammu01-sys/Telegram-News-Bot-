from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup
import feedparser
from app.scrapers.base_scraper import BaseScraper
from app.utils.logger import logger

RSS_URL = "https://cointelegraph.com/rss"


class CoinTelegraphScraper(BaseScraper):
    source_name = "CoinTelegraph"

    def scrape(self) -> list[dict]:
        logger.info("CoinTelegraph: starting scrape via RSS")
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

        try:
            feed = feedparser.parse(RSS_URL)
        except Exception as e:
            logger.error(f"CoinTelegraph: failed to parse RSS feed — {e}")
            return []

        if feed.bozo and not feed.entries:
            logger.error(f"CoinTelegraph: RSS feed returned no entries — {feed.bozo_exception}")
            return []

        articles = []
        for entry in feed.entries:
            article = self._parse_entry(entry, cutoff)
            if article:
                articles.append(article)

        logger.info(f"CoinTelegraph: {len(articles)} articles in last 24hrs")
        if not articles:
            logger.warning("CoinTelegraph: 0 articles found in last 24 hours")
        return articles

    def _parse_entry(self, entry: object, cutoff: datetime) -> dict | None:
        # Title
        title = entry.get("title", "").strip()
        if not title:
            return None

        # URL — use guid (clean URL without UTM params)
        url = entry.get("guid", entry.get("link", "")).strip()
        if not url:
            return None
        # Strip any UTM query params from link if guid wasn't available
        if "?" in url and "guid" not in entry:
            url = url.split("?")[0]

        # Timestamp — pubDate is RFC 2822 format
        pub_date_str = entry.get("published", entry.get("updated", ""))
        if not pub_date_str:
            return None

        try:
            pub_dt = parsedate_to_datetime(pub_date_str)
            if pub_dt.tzinfo is None:
                pub_dt = pub_dt.replace(tzinfo=timezone.utc)
            if pub_dt < cutoff:
                return None  # too old
            raw_time = pub_dt.isoformat()
        except Exception:
            return None

        # Content — extract text from HTML description
        description_html = entry.get("description", entry.get("summary", ""))
        content = BeautifulSoup(description_html, "lxml").get_text(separator=" ", strip=True)

        return {
            "title":       title,
            "url":         url,
            "content":     content,
            "timestamp":   raw_time,
            "source_name": self.source_name,
        }
