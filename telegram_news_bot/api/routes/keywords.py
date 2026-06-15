# file: d:/Telegram-Bot/telegram_news_bot/api/routes/keywords.py
from fastapi import APIRouter, HTTPException, Path, Body, Response, status
from pydantic import BaseModel, Field
from typing import Optional, List
from ...database.client import supabase

router = APIRouter(
    tags=["keywords"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)

class KeywordCreate(BaseModel):
    word: str = Field(..., example="blockchain")
    category_id: int = Field(..., example=2)

class KeywordUpdate(BaseModel):
    word: Optional[str] = Field(None, example="crypto")
    category_id: Optional[int] = Field(None, example=3)

@router.get(
    "/",
    summary="List all keywords",
)
def list_keywords():
    try:
        resp = (
            supabase.table("keywords")
            .select("*, categories(name)")
            .execute()
        )
        return resp.data
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new keyword",
)
def create_keyword(body: KeywordCreate = Body(...)):
    try:
        resp = supabase.table("keywords").insert(body.model_dump()).execute()
        return resp.data[0]
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.put(
    "/{keyword_id}",
    summary="Update an existing keyword",
)
def update_keyword(
    keyword_id: int = Path(..., description="Keyword ID", example=1),
    body: KeywordUpdate = Body(...),
):
    try:
        update_data = {k: v for k, v in body.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        resp = (
            supabase.table("keywords")
            .update(update_data)
            .eq("id", keyword_id)
            .execute()
        )
        if not resp.data:
            raise HTTPException(status_code=404, detail="Keyword not found")
        return resp.data[0]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.delete(
    "/{keyword_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a keyword",
    responses={status.HTTP_204_NO_CONTENT: {"description": "Keyword deleted"}},
)
def delete_keyword(
    keyword_id: int = Path(..., description="Keyword ID", example=1)
):
    try:
        resp = (
            supabase.table("keywords")
            .delete()
            .eq("id", keyword_id)
            .execute()
        )
        delete_success = resp.data and len(resp.data) > 0
        if not delete_success:
            raise HTTPException(status_code=404, detail="Keyword not found")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
