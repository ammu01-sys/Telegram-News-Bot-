from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database.client import get_client

router = APIRouter()


class KeywordCreate(BaseModel):
    word: str
    category_id: str


@router.get("/")
def list_keywords():
    db = get_client()
    return db.table("keywords").select("*, categories(name)").order("word").execute().data


@router.post("/")
def create_keyword(body: KeywordCreate):
    db = get_client()
    return db.table("keywords").insert(body.model_dump()).execute().data


@router.delete("/{kw_id}")
def delete_keyword(kw_id: str):
    db = get_client()
    db.table("keywords").delete().eq("id", kw_id).execute()
    return {"deleted": kw_id}
