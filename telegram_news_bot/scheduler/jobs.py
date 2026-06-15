from threading import Lock
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from ..utils.config import SCRAPE_INTERVAL_MINUTES
from ..utils.logger import get_logger
from ..scrapers import cointelegraph, blockworks, cnbc, medicalnewstoday
from ..services.cleaner import clean_article
from ..services.classifier import classify, classifier as clf
from ..services.dispatcher import dispatch_all
from ..services.rephraser import reset_quota_flag
from ..database.queries import (
    get_source_id_by_name,
    insert_article,
    update_article_status,
    get_source_last_scraped,
    update_source_last_scraped,
)
from ..database.client import supabase

logger = get_logger(__name__)

scheduler = BackgroundScheduler()
_pipeline_lock = Lock()


def run_pipeline() -> None:
    if not _pipeline_lock.acquire(blocking=False):
        logger.warning("Pipeline already running — skipping overlapping run")
        return

    try:
        reset_quota_flag()
        clf.refresh()
        logger.info("Pipeline started")
        total_scraped = 0
        total_inserted = 0

        scrapers = [
            ("CoinTelegraph", cointelegraph.scrape),
            ("Blockworks", blockworks.scrape),
            ("CNBC", cnbc.scrape),
            ("Medical News Today", medicalnewstoday.scrape),
        ]

        for source_name, scrape_func in scrapers:
            try:
                articles = scrape_func()
                total_scraped += len(articles)

                source_id = get_source_id_by_name(source_name)
                if source_id is None:
                    logger.warning(f"Source '{source_name}' not found in DB, skipping")
                    continue

                last_scraped_at = get_source_last_scraped(source_id)

                for article in articles:
                    # Skip articles older than last scrape for this source
                    published_at = article.get("published_at")
                    if published_at and last_scraped_at and published_at <= last_scraped_at:
                        continue

                    cleaned = clean_article(article)
                    cleaned["source_id"] = source_id
                    cleaned.pop("source_name", None)

                    category_id = classify(cleaned.get("content", ""))
                    cleaned["category_id"] = category_id

                    article_id = insert_article(cleaned)
                    if article_id:
                        total_inserted += 1
                        update_article_status(article_id, "classified")

                update_source_last_scraped(source_id)
            except Exception as e:
                logger.error(f"Pipeline error for {source_name}: {e}")

        dispatch_result = dispatch_all()

        logger.info(
            f"Pipeline complete: scraped {total_scraped}, "
            f"inserted {total_inserted}, "
            f"dispatched {dispatch_result.get('success', 0)}"
        )
    finally:
        _pipeline_lock.release()


def start_scheduler() -> None:
    interval = max(SCRAPE_INTERVAL_MINUTES, 1)
    scheduler.add_job(run_pipeline, "interval", minutes=interval, id="pipeline")
    scheduler.start()
    logger.info(f"Scheduler started - running every {interval} minute(s)")


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
