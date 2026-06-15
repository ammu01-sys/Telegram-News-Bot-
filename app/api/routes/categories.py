from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.database.client import get_client

router = APIRouter()


class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None


@router.get("/")
def list_categories():
    db = get_client()
    return db.table("categories").select("*").order("name").execute().data


@router.post("/")
def create_category(body: CategoryCreate):
    db = get_client()
    return db.table("categories").insert(body.model_dump()).execute().data


@router.put("/{cat_id}")
def update_category(cat_id: str, body: CategoryCreate):
    db = get_client()
    result = db.table("categories").update(body.model_dump()).eq("id", cat_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Category not found")
    return result.data


@router.delete("/{cat_id}")
def delete_category(cat_id: str):
    db = get_client()
    db.table("categories").delete().eq("id", cat_id).execute()
    return {"deleted": cat_id}
