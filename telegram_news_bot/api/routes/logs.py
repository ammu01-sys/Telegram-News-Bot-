from fastapi import APIRouter, Query
from typing import Optional
from ...database.client import supabase

router = APIRouter()


@router.get("/")
def list_logs(
    event_type: Optional[str] = Query(default=None),
    limit: int = Query(default=200, le=2000),
):
    query = supabase.table("logs").select("*").order("posted_at", desc=True)
    if event_type:
        query = query.eq("status", event_type)
    query = query.limit(limit)
    result = query.execute()
    return result.data if result else []
