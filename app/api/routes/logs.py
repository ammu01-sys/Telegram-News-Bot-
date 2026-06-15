from fastapi import APIRouter, Query
from typing import Optional
from app.database.client import get_client

router = APIRouter()


@router.get("/")
def list_logs(
    event_type: Optional[str] = Query(None),
    limit: int = Query(300, ge=1, le=2000),
):
    db = get_client()
    q = db.table("logs").select("*").order("created_at", desc=True).limit(limit)

    if event_type:
        q = q.eq("event_type", event_type)

    return q.execute().data
