from datetime import datetime, timedelta, timezone
import feedparser
from app.scrapers.base_scraper import BaseScraper
from app.utils.logger import logger

RSS_URL = "https://blockworks.co/rss"


class BlockworksScraper(BaseScraper):
    source_name = "Blockworks"

    def scrape(self) -> list[dict]:
        logger.info("Blockworks: starting scrape via Atom feed")
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

        try:
            feed = feedparser.parse(RSS_URL)
        except Exception as e:
            logger.error(f"Blockworks: failed to parse Atom feed — {e}")
            return []

        if feed.bozo and not feed.entries:
            logger.error(f"Blockworks: Atom feed returned no entries — {feed.bozo_exception}")
            return []

        articles = []
        for entry in feed.entries:
            article = self._parse_entry(entry, cutoff)
            if article:
                articles.append(article)

        logger.info(f"Blockworks: {len(articles)} articles in last 24hrs")
        if not articles:
            logger.warning("Blockworks: 0 articles found in last 24 hours")
        return articles

    def _parse_entry(self, entry: object, cutoff: datetime) -> dict | None:
        # Title
        title = entry.get("title", "").strip()
        if not title:
            return None

        # URL — Atom uses <link href="..."> or <id>
        url = entry.get("link", entry.get("id", "")).strip()
        if not url:
            return None

        # Timestamp — Atom uses <published> or <updated> in ISO 8601
        pub_date_str = entry.get("published", entry.get("updated", ""))
        if not pub_date_str:
            return None

        try:
            pub_dt = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
            if pub_dt < cutoff:
                return None  # too old
            raw_time = pub_dt.isoformat()
        except Exception:
            return None

        # Content — Atom entries have <summary> and/or <content>
        content = entry.get("summary", entry.get("content", [{}])[0].get("value", "") if entry.get("content") else "")
        content = content.strip() if content else title  # fallback to title if empty

        return {
            "title":       title,
            "url":         url,
            "content":     content,
            "timestamp":   raw_time,
            "source_name": self.source_name,
        }
