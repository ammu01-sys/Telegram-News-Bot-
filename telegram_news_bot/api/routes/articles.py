from fastapi import APIRouter, Query
from ...database.queries import get_all_articles, get_unposted_articles, get_posting_history, get_posting_stats

router = APIRouter()


@router.get("/")
def list_articles(limit: int = Query(default=100, le=1000)):
    return get_all_articles(limit)


@router.get("/unposted")
def list_unposted():
    return get_unposted_articles()


@router.get("/history")
def list_history(limit: int = Query(default=100, le=500)):
    return get_posting_history(limit)


@router.get("/stats")
def stats():
    return get_posting_stats()
