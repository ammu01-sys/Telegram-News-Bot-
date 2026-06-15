from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.database.client import get_client

router = APIRouter()


class ChannelCreate(BaseModel):
    telegram_id: str
    name: Optional[str] = None
    is_active: bool = True
    source_filter: str


@router.get("/")
def list_channels():
    db = get_client()
    return db.table("channels").select("*").order("name").execute().data


@router.post("/")
def create_channel(body: ChannelCreate):
    db = get_client()
    return db.table("channels").insert(body.model_dump()).execute().data


@router.put("/{ch_id}")
def update_channel(ch_id: str, body: ChannelCreate):
    db = get_client()
    result = db.table("channels").update(body.model_dump()).eq("id", ch_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Channel not found")
    return result.data


@router.delete("/{ch_id}")
def delete_channel(ch_id: str):
    db = get_client()
    db.table("channels").delete().eq("id", ch_id).execute()
    return {"deleted": ch_id}
