# 🕷️ PHASE 2 — Scraping & Data Pipeline
> **Scope:** Supabase client, scrapers, cleaner, deduplication, classifier, storage
> **Milestone:** 1 (tasks 3–7)
> **Outcome:** Articles from both websites are scraped, cleaned, classified, and stored in Supabase without duplicates
> **Estimated effort:** Day 2–3

---

## 🎯 GOAL OF THIS PHASE

Build the data intake pipeline. By the end of this phase you can run a single function and:
1. Fetch the last 24 hours of articles from both websites
2. Clean them
3. Skip duplicates
4. Assign a category
5. Store them in Supabase

No posting yet. No AI yet. Just clean data flowing into the database.

---

## ✅ TASK CHECKLIST

- [ ] 2.1 — Supabase client (`database/client.py`)
- [ ] 2.2 — Pydantic models (`database/models.py`)
- [ ] 2.3 — DB query functions (`database/queries.py`)
- [ ] 2.4 — BaseScraper abstract class (`scrapers/base_scraper.py`)
- [ ] 2.5 — CoinTelegraph scraper (`scrapers/cointelegraph.py`)
- [ ] 2.6 — Blockworks scraper (`scrapers/blockworks.py`)
- [ ] 2.7 — Data cleaner (`services/cleaner.py`)
- [ ] 2.8 — Classifier (`services/classifier.py`)
- [ ] 2.9 — Manual test: run both scrapers, verify DB rows

---

## 📄 FILE: `app/database/client.py`

```python
from supabase import create_client, Client
from app.utils.config import SUPABASE_URL, SUPABASE_KEY

_client: Client | None = None

def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client
```

---

## 📄 FILE: `app/database/models.py`

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ArticleModel(BaseModel):
    title:        str
    url:          str
    content:      str
    source_name:  str
    category_id:  Optional[str] = None
    is_posted:    bool = False
    published_at: Optional[datetime] = None

class LogModel(BaseModel):
    event_type: str                   # SCRAPE | POST | ERROR | CLASSIFY | AI
    message:    str
    article_id: Optional[str] = None
```

---

## 📄 FILE: `app/database/queries.py`

```python
from datetime import datetime, timedelta, timezone
from app.database.client import get_client
from app.utils.logger import logger

def insert_article(data: dict) -> bool:
    """Insert article. Returns True if inserted, False if duplicate."""
    try:
        db = get_client()
        db.table("articles").insert(data).execute()
        return True
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            return False          # silent skip — URL already exists
        logger.error(f"DB insert error: {e}")
        return False

def get_unposted_articles() -> list[dict]:
    """Return all unposted articles published in last 24 hours."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    db = get_client()
    result = (
        db.table("articles")
        .select("*, categories(name)")
        .eq("is_posted", False)
        .gte("published_at", cutoff)
        .execute()
    )
    return result.data or []

def mark_as_posted(article_id: str) -> None:
    db = get_client()
    db.table("articles").update({"is_posted": True}).eq("id", article_id).execute()

def get_keywords_with_categories() -> list[dict]:
    """Return all keywords joined with their category name."""
    db = get_client()
    result = db.table("keywords").select("word, categories(name)").execute()
    return result.data or []

def get_active_channels() -> list[dict]:
    db = get_client()
    result = db.table("channels").select("*").eq("is_active", True).execute()
    return result.data or []

def insert_log(event_type: str, message: str, article_id: str = None) -> None:
    db = get_client()
    payload = {"event_type": event_type, "message": message}
    if article_id:
        payload["article_id"] = article_id
    try:
        db.table("logs").insert(payload).execute()
    except Exception as e:
        logger.error(f"Failed to write log: {e}")
```

---

## 📄 FILE: `app/scrapers/base_scraper.py`

```python
from abc import ABC, abstractmethod

class BaseScraper(ABC):
    """
    All scrapers inherit from this.
    scrape() must return a list of dicts with these exact keys:
      - title       (str)
      - url         (str)   ← unique identifier, used for deduplication
      - content     (str)   ← full article body, HTML stripped by cleaner later
      - timestamp   (str)   ← raw timestamp string, normalized by cleaner later
      - source_name (str)   ← hardcoded per scraper, e.g. 'CoinTelegraph'
    """

    @abstractmethod
    def scrape(self) -> list[dict]:
        pass

    def _safe_get(self, url: str, headers: dict = None, retries: int = 2) -> object | None:
        """HTTP GET with retry. Returns Response or None."""
        import requests, time
        for attempt in range(retries + 1):
            try:
                resp = requests.get(url, headers=headers or {}, timeout=15)
                resp.raise_for_status()
                return resp
            except Exception as e:
                if attempt < retries:
                    time.sleep(3)
                else:
                    return None
```

---

## 📄 FILE: `app/scrapers/cointelegraph.py`

```python
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
from app.scrapers.base_scraper import BaseScraper
from app.utils.logger import logger

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)"}
BASE_URL = "https://cointelegraph.com"

class CoinTelegraphScraper(BaseScraper):
    source_name = "CoinTelegraph"

    def scrape(self) -> list[dict]:
        logger.info("CoinTelegraph: starting scrape")
        resp = self._safe_get(BASE_URL, headers=HEADERS)
        if not resp:
            logger.error("CoinTelegraph: failed to fetch homepage")
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        articles = []

        # CoinTelegraph article links are in <a> tags with class containing 'post-card'
        # Adjust selector if site structure changes
        links = soup.select("a.post-card-inline__title-link, a[class*='post-card']")

        for link in links[:30]:  # check top 30, filter by date
            href = link.get("href", "")
            if not href.startswith("http"):
                href = BASE_URL + href

            article = self._fetch_article(href, cutoff)
            if article:
                articles.append(article)

        logger.info(f"CoinTelegraph: {len(articles)} articles in last 24hrs")
        if not articles:
            logger.warning("CoinTelegraph: 0 articles found in last 24 hours")
        return articles

    def _fetch_article(self, url: str, cutoff: datetime) -> dict | None:
        resp = self._safe_get(url, headers=HEADERS)
        if not resp:
            return None

        soup = BeautifulSoup(resp.text, "lxml")

        # Title
        title_tag = soup.select_one("h1.post__title, h1")
        title = title_tag.get_text(strip=True) if title_tag else ""
        if not title:
            return None

        # Timestamp — look for <time> tag with datetime attribute
        time_tag = soup.select_one("time[datetime]")
        raw_time = time_tag["datetime"] if time_tag else ""
        if not raw_time:
            return None

        # Parse and filter by 24hr window
        try:
            pub_dt = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
            if pub_dt < cutoff:
                return None  # too old
        except Exception:
            return None

        # Content
        content_div = soup.select_one("div.post-content, article")
        content = content_div.get_text(separator=" ", strip=True) if content_div else ""

        return {
            "title":       title,
            "url":         url,
            "content":     content,
            "timestamp":   raw_time,
            "source_name": self.source_name,
        }
```

---

## 📄 FILE: `app/scrapers/blockworks.py`

```python
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
from app.scrapers.base_scraper import BaseScraper
from app.utils.logger import logger

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)"}
BASE_URL = "https://blockworks.co"
NEWS_URL = "https://blockworks.co/news"

class BlockworksScraper(BaseScraper):
    source_name = "Blockworks"

    def scrape(self) -> list[dict]:
        logger.info("Blockworks: starting scrape")
        resp = self._safe_get(NEWS_URL, headers=HEADERS)
        if not resp:
            logger.error("Blockworks: failed to fetch news page")
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        articles = []

        # Blockworks article links — adjust selector if structure changes
        links = soup.select("a[href*='/news/']")
        seen = set()

        for link in links[:30]:
            href = link.get("href", "")
            if not href.startswith("http"):
                href = BASE_URL + href
            if href in seen:
                continue
            seen.add(href)

            article = self._fetch_article(href, cutoff)
            if article:
                articles.append(article)

        logger.info(f"Blockworks: {len(articles)} articles in last 24hrs")
        if not articles:
            logger.warning("Blockworks: 0 articles found in last 24 hours")
        return articles

    def _fetch_article(self, url: str, cutoff: datetime) -> dict | None:
        resp = self._safe_get(url, headers=HEADERS)
        if not resp:
            return None

        soup = BeautifulSoup(resp.text, "lxml")

        title_tag = soup.select_one("h1")
        title = title_tag.get_text(strip=True) if title_tag else ""
        if not title:
            return None

        time_tag = soup.select_one("time[datetime]")
        raw_time = time_tag["datetime"] if time_tag else ""
        if not raw_time:
            return None

        try:
            pub_dt = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
            if pub_dt < cutoff:
                return None
        except Exception:
            return None

        content_div = soup.select_one("article, div[class*='content'], div[class*='body']")
        content = content_div.get_text(separator=" ", strip=True) if content_div else ""

        return {
            "title":       title,
            "url":         url,
            "content":     content,
            "timestamp":   raw_time,
            "source_name": self.source_name,
        }
```

---

## 📄 FILE: `app/services/cleaner.py`

```python
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
```

---

## 📄 FILE: `app/services/classifier.py`

```python
from app.database.queries import get_keywords_with_categories, insert_log
from app.utils.logger import logger

def classify_article(content: str, title: str) -> tuple[str | None, str]:
    """
    Match article content+title against keywords.
    Returns (category_name, category_id) or (None, None) if unmatched.
    First match wins — single category per article.
    """
    keywords = get_keywords_with_categories()
    text = (title + " " + content).lower()

    for kw in keywords:
        word = kw.get("word", "").lower()
        if word and word in text:
            cat_name = kw["categories"]["name"]
            return cat_name
    return None

def get_category_id(category_name: str) -> str | None:
    """Look up category UUID by name."""
    from app.database.client import get_client
    if not category_name:
        return None
    db = get_client()
    result = db.table("categories").select("id").eq("name", category_name).execute()
    rows = result.data or []
    return rows[0]["id"] if rows else None
```

---

## 🔄 PIPELINE RUNNER (manual test script)

Create `run_pipeline_test.py` at project root to test this phase manually:

```python
"""
Run this manually to test Phase 2 end-to-end.
python run_pipeline_test.py
"""
from app.scrapers.cointelegraph import CoinTelegraphScraper
from app.scrapers.blockworks import BlockworksScraper
from app.services.cleaner import clean_article
from app.services.classifier import classify_article, get_category_id
from app.database.queries import insert_article, insert_log

def run():
    scrapers = [CoinTelegraphScraper(), BlockworksScraper()]

    for scraper in scrapers:
        articles = scraper.scrape()

        for raw in articles:
            # 1. Clean
            cleaned = clean_article(raw)

            # 2. Classify
            category_name = classify_article(cleaned["content"], cleaned["title"])
            category_id   = get_category_id(category_name)

            if not category_name:
                insert_log("CLASSIFY", f"No category match for: {cleaned['title'][:60]}")

            # 3. Store (skip if duplicate)
            payload = {
                "title":        cleaned["title"],
                "url":          cleaned["url"],
                "content":      cleaned["content"],
                "source_name":  cleaned["source_name"],
                "category_id":  category_id,
                "published_at": cleaned["published_at"],
            }
            inserted = insert_article(payload)
            status = "inserted" if inserted else "duplicate/skipped"
            print(f"[{status}] {cleaned['title'][:60]}")

        insert_log("SCRAPE", f"{scraper.source_name}: {len(articles)} articles scraped")

if __name__ == "__main__":
    run()
```

---

## ✅ VERIFICATION STEPS

After running `python run_pipeline_test.py`:

1. Check terminal output — articles should show `[inserted]` or `[duplicate/skipped]`
2. Open Supabase → `articles` table → rows should be present
3. Run again immediately → all rows should show `[duplicate/skipped]` (dedup working)
4. Check `category_id` column — most should be filled, some may be NULL (Uncategorized)
5. Check `logs` table → SCRAPE events should be logged

---

## 🚦 EXIT CRITERIA (Phase 2 is done when)

- [ ] Both scrapers return non-empty lists (unless truly no articles in 24hrs)
- [ ] Articles older than 24hrs are skipped by scrapers
- [ ] Running twice produces no duplicate DB rows
- [ ] `category_id` is populated for keyword-matched articles
- [ ] Unmatched articles have a CLASSIFY log entry
- [ ] `published_at` is a valid UTC timestamp on every row

---

## ➡️ NEXT PHASE

Once this phase is done → move to **PHASE 3: AI Rephrasing, Posting & Automation**
