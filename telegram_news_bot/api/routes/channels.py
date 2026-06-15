# file: d:/Telegram-Bot/telegram_news_bot/api/routes/channels.py
from fastapi import APIRouter, HTTPException, Path, Body, Response, status
from pydantic import BaseModel, Field
from typing import Optional, List
from ...database.client import supabase

router = APIRouter(
    tags=["channels"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)

class ChannelCreate(BaseModel):
    name: str = Field(..., example="Tech News")
    telegram_chat_id: str = Field(..., example="-1001234567890")
    category_id: Optional[int] = Field(None, example=2)
    is_active: bool = Field(True, example=True)

class ChannelUpdate(BaseModel):
    name: Optional[str] = Field(None, example="Finance Updates")
    telegram_chat_id: Optional[str] = Field(None, example="-1009876543210")
    category_id: Optional[int] = Field(None, example=3)
    is_active: Optional[bool] = Field(None, example=False)

@router.get(
    "/",
    summary="List all channels",
)
def list_channels():
    try:
        resp = (
            supabase.table("channels")
            .select("*, categories(name)")
            .execute()
        )
        return resp.data
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new channel",
)
def create_channel(body: ChannelCreate = Body(...)):
    try:
        resp = supabase.table("channels").insert(body.model_dump()).execute()
        return resp.data[0]
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.put(
    "/{channel_id}",
    summary="Update an existing channel",
)
def update_channel(
    channel_id: int = Path(..., description="Channel ID", example=1),
    body: ChannelUpdate = Body(...),
):
    try:
        update_data = {k: v for k, v in body.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        resp = (
            supabase.table("channels")
            .update(update_data)
            .eq("id", channel_id)
            .execute()
        )
        if not resp.data:
            raise HTTPException(status_code=404, detail="Channel not found")
        return resp.data[0]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.delete(
    "/{channel_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a channel",
    responses={status.HTTP_204_NO_CONTENT: {"description": "Channel deleted"}},
)
def delete_channel(
    channel_id: int = Path(..., description="Channel ID", example=1)
):
    try:
        resp = (
            supabase.table("channels")
            .delete()
            .eq("id", channel_id)
            .execute()
        )
        delete_success = resp.data and len(resp.data) > 0
        if not delete_success:
            raise HTTPException(status_code=404, detail="Channel not found")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
