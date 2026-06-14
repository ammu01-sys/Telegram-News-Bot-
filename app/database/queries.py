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
        .gte("published_at", cutoff)
        .execute()
    )
    articles = result.data or []
    return [a for a in articles if not a.get("is_posted")]


def mark_as_posted(article_id: str) -> None:
    db = get_client()
    db.table("articles").update({"is_posted": True}).eq("id", article_id).execute()


def get_keywords_with_categories() -> list[dict]:
    """Return all keywords joined with their category name."""
    db = get_client()
    result = db.table("keywords").select("word, categories(name)").execute()
    return result.data or []


def get_all_keywords() -> list[dict]:
    """Return all keywords with category_id and category name (single fetch for classification)."""
    db = get_client()
    result = db.table("keywords").select("word, category_id, categories(name)").execute()
    return result.data or []


def get_active_channels() -> list[dict]:
    """Return all active channels. Filters in Python to avoid PostgREST boolean quirks."""
    db = get_client()
    result = db.table("channels").select("*").execute()
    channels = result.data or []
    logger.info(f"Raw channels from DB: {channels}")
    active = [ch for ch in channels if ch.get("is_active")]
    logger.info(f"Active channels after filter: {len(active)}")
    return active


def insert_log(event_type: str, message: str, article_id: str = None) -> None:
    db = get_client()
    payload = {"event_type": event_type, "message": message}
    if article_id:
        payload["article_id"] = article_id
    try:
        db.table("logs").insert(payload).execute()
    except Exception as e:
        logger.error(f"Failed to write log: {e}")
