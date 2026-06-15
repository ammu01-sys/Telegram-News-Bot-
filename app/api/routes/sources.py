from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.database.client import get_client

router = APIRouter()


class SourceCreate(BaseModel):
    name: str
    type: Optional[str] = None
    is_active: bool = True


@router.get("/")
def list_sources():
    db = get_client()
    return db.table("sources").select("*").order("name").execute().data


@router.post("/")
def create_source(body: SourceCreate):
    db = get_client()
    return db.table("sources").insert(body.model_dump()).execute().data


@router.put("/{source_id}")
def update_source(source_id: str, body: SourceCreate):
    db = get_client()
    result = db.table("sources").update(body.model_dump()).eq("id", source_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Source not found")
    return result.data


@router.delete("/{source_id}")
def delete_source(source_id: str):
    db = get_client()
    db.table("sources").delete().eq("id", source_id).execute()
    return {"deleted": source_id}
