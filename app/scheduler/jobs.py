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
        from app.database.queries import insert_article, get_all_keywords, upsert_source
    
        # Fetch keywords ONCE — each entry has word, category_id, categories(name)
        keywords = get_all_keywords()
    
        scrapers = [CoinTelegraphScraper(), BlockworksScraper()]
        total_new = 0
    
        for scraper in scrapers:
            articles = scraper.scrape()
            new_count = 0
    
            for raw in articles:
                cleaned = clean_article(raw)
    
                # Register newly discovered article source in sources table
                article_source = cleaned.get("article_source", "")
                if article_source:
                    upsert_source(article_source)
    
                # Combine title + content, lowercase once
                text = (cleaned["title"] + " " + cleaned["content"]).lower()
    
                # First keyword match wins — maps directly to category UUID
                category_id = None
                for kw in keywords:
                    if kw.get("word", "").lower() in text:
                        category_id = kw["category_id"]
                        break
    
                if not category_id:
                    insert_log(
                        "CLASSIFY",
                        f"No keyword match — '{cleaned['title'][:50]}'",
                    )
    
                payload = {
                    "title":          cleaned["title"],
                    "url":            cleaned["url"],
                    "content":        cleaned["content"],
                    "source_name":    cleaned["source_name"],
                    "article_source": cleaned.get("article_source", ""),
                    "category_id":    category_id,
                    "published_at":   cleaned["published_at"],
                }
                inserted = insert_article(payload)
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
