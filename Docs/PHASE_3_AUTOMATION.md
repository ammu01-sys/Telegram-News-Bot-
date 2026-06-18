# 🤖 PHASE 3 — AI Rephrasing, Posting & Automation
> **Scope:** AI rephraser, Telegram poster, dispatcher, scheduler, error handling, logging
> **Milestone:** 2 (tasks 10–15)
> **Outcome:** Articles are automatically rephrased in English and posted to the correct Telegram channel. The pipeline runs on server boot and every 60 minutes.
> **Estimated effort:** Day 4–5

---

## 🎯 GOAL OF THIS PHASE

By the end of this phase, the system runs without any human involvement:

1. Server starts → scheduler fires immediately
2. Scrapers run → articles stored (Phase 2 logic)
3. Rephraser summarizes each article in English via Gemini → Groq → raw fallback
4. Dispatcher matches articles to their correct channel by source
5. Telegram bot posts the formatted message
6. Every event — success or failure — is logged with a reason

---

## ✅ TASK CHECKLIST

- [ ] 3.1 — AI rephraser with Gemini → Groq → raw fallback (`services/rephraser.py`)
- [ ] 3.2 — Telegram poster with 3x retry (`services/poster.py`)
- [ ] 3.3 — Dispatcher with source-to-channel matching (`services/dispatcher.py`)
- [ ] 3.4 — Logger setup (`utils/logger.py`)
- [ ] 3.5 — Scheduler with FastAPI lifespan boot (`scheduler/jobs.py`)
- [ ] 3.6 — Wire everything in `app/main.py`
- [ ] 3.7 — Manual end-to-end test

---

## 📄 FILE: `app/utils/logger.py`

```python
import logging
from app.utils.config import LOG_LEVEL

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("newsbot")
```

---

## 📄 FILE: `app/services/rephraser.py`

```python
import time
import google.generativeai as genai
from groq import Groq
from app.utils.config import GEMINI_API_KEY, GROQ_API_KEY
from app.utils.logger import logger
from app.database.queries import insert_log

PROMPT_TEMPLATE = """
Summarize the following crypto news article in exactly 3 sentences in English.
Be concise, factual, and suitable for a Telegram news channel.
Do not add opinions. Output only the 3-sentence summary, nothing else.

Title: {title}
Content: {content}
""".strip()

def rephrase(title: str, content: str, article_id: str = None) -> str:
    """
    Try Gemini → Groq → raw fallback.
    Always returns a non-empty string in English.
    """
    prompt = PROMPT_TEMPLATE.format(title=title, content=content[:2000])

    # ── Try Gemini ─────────────────────────────────
    result = _try_gemini(prompt)
    if result:
        return result

    insert_log("AI", "Gemini failed — trying Groq", article_id)

    # ── Try Groq ───────────────────────────────────
    result = _try_groq(prompt)
    if result:
        return result

    insert_log("AI", "Groq failed — using raw content fallback", article_id)

    # ── Raw fallback ───────────────────────────────
    return content[:300].strip() + "..."


def _try_gemini(prompt: str) -> str | None:
    for attempt in range(2):
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            model  = genai.GenerativeModel("gemini-1.5-flash")
            resp   = model.generate_content(prompt)
            text   = resp.text.strip()
            if text:
                return text
        except Exception as e:
            logger.warning(f"Gemini attempt {attempt+1} failed: {e}")
            time.sleep(3)
    return None


def _try_groq(prompt: str) -> str | None:
    for attempt in range(2):
        try:
            client = Groq(api_key=GROQ_API_KEY)
            chat   = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
            )
            text = chat.choices[0].message.content.strip()
            if text:
                return text
        except Exception as e:
            logger.warning(f"Groq attempt {attempt+1} failed: {e}")
            time.sleep(3)
    return None
```

---

## 📄 FILE: `app/services/poster.py`

```python
import time
import requests
from app.utils.config import TELEGRAM_BOT_TOKEN
from app.utils.logger import logger
from app.database.queries import insert_log

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

def post_to_telegram(article: dict, channel_id: str, summary: str) -> bool:
    """
    Post article to a specific Telegram channel.
    Retries 3 times on failure.
    Returns True on success, False after all retries fail.
    """
    message = _format_message(article["title"], summary, article["url"])

    for attempt in range(1, 4):  # 3 attempts
        try:
            resp = requests.post(
                TELEGRAM_API,
                json={
                    "chat_id":    channel_id,
                    "text":       message,
                    "parse_mode": "HTML",
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get("ok"):
                logger.info(f"Posted to {channel_id}: {article['title'][:50]}")
                return True
            else:
                raise Exception(f"Telegram API error: {data}")

        except Exception as e:
            logger.warning(f"Post attempt {attempt}/3 failed for {channel_id}: {e}")
            if attempt < 3:
                time.sleep(5)

    # All 3 attempts failed
    insert_log(
        "ERROR",
        f"POST FAILED after 3 retries — channel: {channel_id} — reason: final attempt failed",
        article.get("id"),
    )
    return False


def _format_message(title: str, summary: str, url: str) -> str:
    return f"📰 <b>{title}</b>\n\n{summary}\n\n🔗 {url}"
```

---

## 📄 FILE: `app/services/dispatcher.py`

```python
from app.database.queries import (
    get_unposted_articles,
    get_active_channels,
    mark_as_posted,
    insert_log,
)
from app.services.rephraser import rephrase
from app.services.poster import post_to_telegram
from app.utils.logger import logger


def run_dispatch() -> None:
    """
    For each unposted article from the last 24hrs:
    1. Find the matching active channel (by source_filter == source_name)
    2. Rephrase with AI
    3. Post to Telegram
    4. Mark as posted + log result
    """
    articles = get_unposted_articles()
    channels = get_active_channels()

    if not articles:
        logger.info("Dispatcher: no unposted articles to process")
        return

    if not channels:
        logger.warning("Dispatcher: no active channels found")
        return

    logger.info(f"Dispatcher: processing {len(articles)} articles")

    for article in articles:
        source = article.get("source_name", "")

        # Find the channel that matches this article's source
        matching_channels = [
            ch for ch in channels
            if ch.get("source_filter", "").lower() == source.lower()
        ]

        if not matching_channels:
            insert_log(
                "ERROR",
                f"No matching channel for source '{source}' — article skipped",
                article.get("id"),
            )
            continue

        # Validate category
        category = article.get("categories", {})
        category_name = category.get("name") if isinstance(category, dict) else None

        if not category_name or category_name == "unknown":
            insert_log(
                "ERROR",
                f"Skipped — no valid category — title: {article['title'][:50]}",
                article.get("id"),
            )
            continue

        # Rephrase article
        summary = rephrase(
            title=article["title"],
            content=article.get("content", ""),
            article_id=article.get("id"),
        )

        # Post to each matching channel (should be exactly 1 per source)
        for channel in matching_channels:
            success = post_to_telegram(
                article=article,
                channel_id=channel["telegram_id"],
                summary=summary,
            )

            if success:
                mark_as_posted(article["id"])
                insert_log(
                    "POST",
                    f"SUCCESS — channel: {channel['telegram_id']} — {article['title'][:50]}",
                    article.get("id"),
                )
            # Failure is already logged inside post_to_telegram
```

---

## 📄 FILE: `app/scheduler/jobs.py`

```python
from apscheduler.schedulers.background import BackgroundScheduler
from app.utils.config import SCRAPE_INTERVAL_MINUTES
from app.utils.logger import logger
from app.database.queries import insert_log


def run_pipeline() -> None:
    """Full pipeline: scrape → clean → classify → store → rephrase → post → log."""
    logger.info("─── Pipeline run started ───")
    insert_log("SCRAPE", "Pipeline run started")

    try:
        # ── Scraping & storage (Phase 2 logic) ──────────
        from app.scrapers.cointelegraph import CoinTelegraphScraper
        from app.scrapers.blockworks import BlockworksScraper
        from app.services.cleaner import clean_article
        from app.services.classifier import classify_article, get_category_id
        from app.database.queries import insert_article

        scrapers = [CoinTelegraphScraper(), BlockworksScraper()]
        total_new = 0

        for scraper in scrapers:
            articles = scraper.scrape()
            new_count = 0

            for raw in articles:
                cleaned       = clean_article(raw)
                category_name = classify_article(cleaned["content"], cleaned["title"])
                category_id   = get_category_id(category_name)

                if not category_name:
                    insert_log(
                        "CLASSIFY",
                        f"No keyword match — '{cleaned['title'][:50]}'",
                    )

                inserted = insert_article({
                    "title":        cleaned["title"],
                    "url":          cleaned["url"],
                    "content":      cleaned["content"],
                    "source_name":  cleaned["source_name"],
                    "category_id":  category_id,
                    "published_at": cleaned["published_at"],
                })
                if inserted:
                    new_count += 1

            insert_log("SCRAPE", f"{scraper.source_name}: {new_count} new articles stored")
            total_new += new_count

        logger.info(f"Scraping done — {total_new} new articles stored")

        # ── Dispatch → AI → Telegram ─────────────────────
        from app.services.dispatcher import run_dispatch
        run_dispatch()

    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        insert_log("ERROR", f"Pipeline crash: {str(e)}")

    logger.info("─── Pipeline run complete ───")


def create_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_pipeline,
        trigger="interval",
        minutes=SCRAPE_INTERVAL_MINUTES,
        id="pipeline_job",
        replace_existing=True,
    )
    return scheduler
```

---

## 📄 FILE: `app/main.py`

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.scheduler.jobs import create_scheduler, run_pipeline
from app.utils.logger import logger

scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────
    global scheduler
    logger.info("Server starting — launching pipeline and scheduler")

    # Run immediately on boot
    run_pipeline()

    # Then schedule recurring runs
    scheduler = create_scheduler()
    scheduler.start()
    logger.info(f"Scheduler started — running every {__import__('app.utils.config', fromlist=['SCRAPE_INTERVAL_MINUTES']).SCRAPE_INTERVAL_MINUTES} minutes")

    yield  # app is live here

    # ── Shutdown ─────────────────────────────────────
    if scheduler:
        scheduler.shutdown()
    logger.info("Server shutting down — scheduler stopped")


app = FastAPI(title="Telegram News Bot API", lifespan=lifespan)

# Register API routes (Phase 4)
from app.api.routes import sources, categories, keywords, channels, articles
app.include_router(sources.router,    prefix="/sources",    tags=["Sources"])
app.include_router(categories.router, prefix="/categories", tags=["Categories"])
app.include_router(keywords.router,   prefix="/keywords",   tags=["Keywords"])
app.include_router(channels.router,   prefix="/channels",   tags=["Channels"])
app.include_router(articles.router,   prefix="/articles",   tags=["Articles"])

@app.get("/")
def health():
    return {"status": "running"}
```

---

## 🔁 RETRY & FALLBACK SUMMARY

```
Scraper HTTP error       → retry 2x (3s gap) → log error, return []
Scraper 0 articles       → log warning "No articles in 24hrs"
Gemini API error         → retry 1x (3s gap) → switch to Groq
Groq API error           → retry 1x (3s gap) → use raw content[:300]
Telegram post error      → retry 3x (5s gap) → log ERROR, skip article
Article no category      → log CLASSIFY error, skip in dispatcher
Article no channel match → log ERROR, skip
```

---

## ✅ VERIFICATION STEPS

1. Start server: `uvicorn app.main:app --reload`
2. Watch terminal — pipeline should run immediately on boot
3. Check Telegram channels — articles should appear
4. Check Supabase `articles` table — `is_posted` should be `TRUE` for posted articles
5. Check Supabase `logs` table — POST SUCCESS entries should be present
6. Kill and restart server — pipeline should run again, but no re-posts (dedup)

---

## 🚦 EXIT CRITERIA (Phase 3 is done when)

- [ ] Pipeline runs on server boot without manual trigger
- [ ] CoinTelegraph articles appear in Channel 1 only
- [ ] Blockworks articles appear in Channel 2 only
- [ ] No article is posted twice
- [ ] Gemini → Groq fallback tested (temporarily use wrong Gemini key)
- [ ] All logs written to Supabase `logs` table with reasons
- [ ] Scheduler confirmed running every 60 minutes

---

## ➡️ NEXT PHASE

Once this phase is done → move to **PHASE 4: FastAPI Routes & Streamlit Dashboard**
