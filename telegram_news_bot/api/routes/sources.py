from fastapi import APIRouter, HTTPException, Path, Body, Response, status
from pydantic import BaseModel, Field
from typing import Optional, List

# Import supabase client and helper queries
from ...database.client import supabase
from ...database.queries import get_all_sources, get_active_sources

router = APIRouter(
    tags=["sources"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)

# ----------------------------------------------------------------------
# Pydantic models – include examples for Swagger UI
# ----------------------------------------------------------------------
class SourceCreate(BaseModel):
    name: str = Field(..., examples=["BBC News"])
    url: str = Field(..., examples=["https://www.bbc.com/news"])
    is_active: bool = Field(True, examples=[True])

class SourceUpdate(BaseModel):
    name: Optional[str] = Field(None, examples=["CNN"])
    url: Optional[str] = Field(None, examples=["https://www.cnn.com"])
    is_active: Optional[bool] = Field(None, examples=[False])

# ----------------------------------------------------------------------
# CRUD endpoints
# ----------------------------------------------------------------------
@router.get(
    "/",
    summary="List all sources",
)
def list_sources():
    """Return every source record (including the related ``is_active`` flag)."""
    return get_all_sources()

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new source",
)
def create_source(
    body: SourceCreate = Body(..., examples=[{"name": "TechCrunch", "url": "https://techcrunch.com", "is_active": True}])
):
    try:
        resp = supabase.table("sources").insert(body.model_dump()).execute()
        return resp.data[0]
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.put(
    "/{source_id}",
    summary="Update a source",
)
def update_source(
    source_id: int = Path(..., description="ID of the source to update", examples=[1]),
    body: SourceUpdate = Body(..., examples=[{"name": "Reuters", "is_active": False}])
):
    try:
        update_data = {k: v for k, v in body.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        resp = supabase.table("sources").update(update_data).eq("id", source_id).execute()
        if not resp.data:
            raise HTTPException(status_code=404, detail="Source not found")
        return resp.data[0]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.delete(
    "/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a source",
    responses={status.HTTP_204_NO_CONTENT: {"description": "Source deleted"}},
)
def delete_source(
    source_id: int = Path(..., description="ID of the source to delete", examples=[1])
):
    try:
        resp = supabase.table("sources").delete().eq("id", source_id).execute()
        delete_success = resp.data and len(resp.data) > 0
        if not delete_success:
            raise HTTPException(status_code=404, detail="Source not found")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
