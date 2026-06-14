from app.database.queries import get_keywords_with_categories, insert_log
from app.utils.logger import logger


def classify_article(content: str, title: str) -> str | None:
    """
    Match article content+title against keywords.
    Returns category_name or None if unmatched.
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
