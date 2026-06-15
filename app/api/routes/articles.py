from fastapi import APIRouter, Query
from typing import Optional
from app.database.client import get_client

router = APIRouter()


@router.get("/")
def list_articles(
    source: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    is_posted: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
):
    db = get_client()

    # Fetch all with join, then filter in Python for reliable boolean handling
    result = (
        db.table("articles")
        .select("*, categories(name)")
        .order("published_at", desc=True)
        .limit(limit)
        .execute()
    )
    articles = result.data or []

    if source:
        articles = [a for a in articles if a.get("source_name", "").lower() == source.lower()]

    if is_posted is not None:
        articles = [a for a in articles if a.get("is_posted") == is_posted]

    if category:
        articles = [
            a for a in articles
            if isinstance(a.get("categories"), dict)
            and a["categories"].get("name", "").lower() == category.lower()
        ]

    return articles
