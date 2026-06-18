import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from ..utils.logger import get_logger
from ..utils.config import MAX_PIPELINE_RETRIES
from ..database.client import supabase

logger = get_logger(__name__)

# Helper to handle supabase execution and errors
def _execute(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Supabase query failed: {e}")
        return None

# ---------------------------------------------------------------------------
# Basic lookup helpers
# ---------------------------------------------------------------------------
def get_active_sources() -> List[Dict[str, Any]]:
    result = _execute(supabase.table("sources").select("*").eq("is_active", True).execute)
    return result.data if result else []

def get_source_id_by_name(name: str) -> Optional[int]:
    result = _execute(
        supabase.table("sources").select("id").eq("name", name).limit(1).execute
    )
    if result and result.data:
        return result.data[0].get("id")
    return None

def get_all_keywords_with_categories() -> List[Dict[str, Any]]:
    result = _execute(
        supabase.table("keywords").select("word, category_id, categories(name)").execute
    )
    return result.data if result else []

def get_active_channels() -> List[Dict[str, Any]]:
    result = _execute(
        supabase.table("channels").select("*, categories(name)").eq("is_active", True).execute
    )
    return result.data if result else []

# ---------------------------------------------------------------------------
# Article handling helpers
# ---------------------------------------------------------------------------
def article_exists(url: str) -> bool:
    """Return True if an article with the given URL already exists in the DB."""
    if not url:
        return False
    result = _execute(
        supabase.table("articles").select("id").eq("url", url).limit(1).execute
    )
    return bool(result and result.data)

def insert_article(data: Dict[str, Any]) -> Optional[int]:
    # Guard against duplicate URLs before inserting
    if article_exists(data.get("url", "")):
        logger.info(f"Duplicate article detected (url={data.get('url')}); skipping insert.")
        return None
    result = _execute(supabase.table("articles").insert(data).execute)
    if result and result.data:
        return result.data[0].get("id")
    # In case Supabase still returns a 409 for a race condition
    if result and getattr(result, "status_code", None) == 409:
        logger.info("Duplicate article (race condition); ignoring.")
    return None

def get_unposted_articles() -> List[Dict[str, Any]]:
    result = _execute(
        supabase.table("articles")
        .select("*, categories(name), sources(name)")
        .in_("status", ["classified", "failed"])
        .order("scraped_at", desc=False)
        .limit(50)
        .execute
    )
    if not result or not result.data:
        return []
    # Filter out articles that have exhausted pipeline retries
    # (if column does not exist yet, .get returns None → 0 → passes through)
    return [a for a in result.data if (a.get("pipeline_retries") or 0) < MAX_PIPELINE_RETRIES]

def increment_pipeline_retries(article_id: int) -> bool:
    current = _execute(
        supabase.table("articles")
        .select("pipeline_retries")
        .eq("id", article_id)
        .limit(1)
        .execute
    )
    val = 0
    if current and current.data:
        val = current.data[0].get("pipeline_retries", 0) or 0
    result = _execute(
        supabase.table("articles")
        .update({"pipeline_retries": val + 1})
        .eq("id", article_id)
        .execute
    )
    return bool(result)

def get_source_last_scraped(source_id: int) -> str | None:
    result = _execute(
        supabase.table("sources")
        .select("last_scraped_at")
        .eq("id", source_id)
        .limit(1)
        .execute
    )
    if result and result.data:
        return result.data[0].get("last_scraped_at")
    return None

def update_source_last_scraped(source_id: int) -> bool:
    now = datetime.utcnow().isoformat()
    result = _execute(
        supabase.table("sources")
        .update({"last_scraped_at": now})
        .eq("id", source_id)
        .execute
    )
    return bool(result)

def update_article_status(article_id: int, status: str, rephrased_content: Optional[str] = None) -> bool:
    data: Dict[str, Any] = {"status": status}
    if rephrased_content:
        data["rephrased_content"] = rephrased_content
    result = _execute(
        supabase.table("articles").update(data).eq("id", article_id).execute
    )
    return bool(result)

def update_article_category(article_id: int, category_id: int) -> bool:
    result = _execute(
        supabase.table("articles").update({"category_id": category_id}).eq("id", article_id).execute
    )
    return bool(result)

# ---------------------------------------------------------------------------
# Channel & posting helpers
# ---------------------------------------------------------------------------
def get_channel_id_by_chat_id(chat_id: str) -> Optional[int]:
    """Return the internal `channels.id` for a given Telegram chat ID."""
    result = _execute(
        supabase.table("channels")
        .select("id")
        .eq("telegram_chat_id", chat_id)
        .limit(1)
        .execute
    )
    if result and result.data:
        return result.data[0].get("id")
    return None

def log_post_attempt(
    article_id: int,
    telegram_chat_id: str,
    status: str,
    error: Optional[str] = None,
    retry_count: int = 0,
) -> None:
    # Resolve internal channel primary key from telegram chat ID
    channel_pk = get_channel_id_by_chat_id(telegram_chat_id)
    _execute(
        supabase.table("logs")
        .insert(
            {
                "article_id": article_id,
                "channel_id": channel_pk,
                "status": status,
                "error": error,
                "retry_count": retry_count,
            }
        )
        .execute
    )

def get_posting_stats() -> Dict[str, int]:
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

    result = _execute(supabase.table("articles").select("id", count="exact").execute)
    total = result.count if result else 0

    result = _execute(
        supabase.table("logs")
        .select("id", count="exact")
        .eq("status", "success")
        .gte("posted_at", today_start)

        .execute
    )
    posted_today = result.count if result else 0

    failed_today = 0
    result = _execute(
        supabase.table("articles")
        .select("id")
        .eq("status", "failed")
        .execute
    )
    if result and result.data:
        failed_today = len(result.data)

    result = _execute(
        supabase.table("sources")
        .select("id", count="exact")
        .eq("is_active", True)
        .execute
    )
    active_sources = result.count if result else 0

    return {
        "total_articles": total,
        "posted_today": posted_today,
        "failed_today": failed_today,
        "active_sources": active_sources,
    }

def get_all_articles(limit: int | None = None) -> List[Dict[str, Any]]:
    query = (
        supabase.table("articles")
        .select("*, categories(name), sources(name)")
        .order("scraped_at", desc=True)
    )
    if limit is not None:
        query = query.limit(limit)
    result = _execute(query.execute)
    return result.data if result else []

def get_posting_history(limit: int | None = None) -> List[Dict[str, Any]]:
    query = (
        supabase.table("logs")
        .select("*, articles(title, url), channels(name)")
        .order("posted_at", desc=True)
    )
    if limit is not None:
        query = query.limit(limit)
    result = _execute(query.execute)
    return result.data if result else []

def get_all_categories_with_keywords() -> List[Dict[str, Any]]:
    result = _execute(
        supabase.table("categories").select("*, keywords(id, word)").execute
    )
    return result.data if result else []

def toggle_source_active(source_id: int, is_active: bool) -> bool:
    result = _execute(
        supabase.table("sources").update({"is_active": is_active}).eq("id", source_id).execute
    )
    return bool(result)

def toggle_channel_active(channel_id: int, is_active: bool) -> bool:
    result = _execute(
        supabase.table("channels").update({"is_active": is_active}).eq("id", channel_id).execute
    )
    return bool(result)

def deactivate_channel(channel_id: int) -> bool:
    """Set channel is_active=False when bot is blocked/kicked."""
    return toggle_channel_active(channel_id, False)

def get_all_sources() -> List[Dict[str, Any]]:
    result = _execute(supabase.table("sources").select("*").order("name").execute)
    return result.data if result else []

def get_all_channels() -> List[Dict[str, Any]]:
    result = _execute(
        supabase.table("channels").select("*, categories(name)").order("name").execute
    )
    return result.data if result else []

def create_source(name: str, url: str) -> Optional[int]:
    result = _execute(supabase.table("sources").insert({"name": name, "url": url}).execute)
    if result and result.data:
        return result.data[0].get("id")
    return None

def create_category(name: str) -> Optional[int]:
    result = _execute(supabase.table("categories").insert({"name": name}).execute)
    if result and result.data:
        return result.data[0].get("id")
    return None

def create_keyword(word: str, category_id: int) -> Optional[int]:
    result = _execute(
        supabase.table("keywords").insert({"word": word, "category_id": category_id}).execute
    )
    if result and result.data:
        return result.data[0].get("id")
    return None

def create_channel(name: str, telegram_chat_id: str, category_id: Optional[int] = None) -> Optional[int]:
    payload: Dict[str, Any] = {"name": name, "telegram_chat_id": telegram_chat_id}
    if category_id is not None:
        payload["category_id"] = category_id
    result = _execute(supabase.table("channels").insert(payload).execute)
    if result and result.data:
        return result.data[0].get("id")
    return None

def delete_record(table: str, record_id: int) -> bool:
    if table not in {"sources", "categories", "keywords", "channels"}:
        logger.error(f"Attempted to delete from unauthorized table: {table}")
        return False
    result = _execute(supabase.table(table).delete().eq("id", record_id).execute)
    return bool(result)

def has_been_posted_to_channel(article_id: int, channel_id: int) -> bool:
    """
    Check if article has already been successfully posted to a specific channel.
    Prevents duplicate posts to the same channel.
    """
    try:
        result = supabase.table("logs")\
            .select("id")\
            .eq("article_id", article_id)\
            .eq("channel_id", channel_id)\
            .eq("status", "success")\
            .limit(1)\
            .execute()
        return len(result.data) > 0
    except Exception as e:
        logger.error(f"has_been_posted_to_channel error: {e}")
        return False

# End of queries module
