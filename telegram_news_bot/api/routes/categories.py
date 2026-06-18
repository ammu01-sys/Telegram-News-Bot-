# Updated categories router with proper OpenAPI definitions
from fastapi import APIRouter, HTTPException, Path, Body, Response, status
from pydantic import BaseModel, Field
from typing import Optional, List
from ...database.client import supabase

router = APIRouter(
    tags=["categories"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)

class CategoryCreate(BaseModel):
    name: str = Field(..., examples=["Tech News"])

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, examples=["Science"])

@router.get("/", summary="List all categories")
def list_categories():
    try:
        resp = supabase.table("categories").select("*, keywords(word)").execute()
        return resp.data
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category",
)
def create_category(body: CategoryCreate = Body(...)):
    try:
        resp = supabase.table("categories").insert(body.model_dump()).execute()
        return resp.data[0]
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.put(
    "/{category_id}",
    summary="Update an existing category",
)
def update_category(
    category_id: int = Path(..., description="Category ID", examples=[1]),
    body: CategoryUpdate = Body(...),
):
    try:
        update_data = {k: v for k, v in body.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        resp = (
            supabase.table("categories")
            .update(update_data)
            .eq("id", category_id)
            .execute()
        )
        if not resp.data:
            raise HTTPException(status_code=404, detail="Category not found")
        return resp.data[0]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a category",
    responses={status.HTTP_204_NO_CONTENT: {"description": "Category deleted"}},
)
def delete_category(
    category_id: int = Path(..., description="Category ID", examples=[1])
):
    try:
        resp = (
            supabase.table("categories")
            .delete()
            .eq("id", category_id)
            .execute()
        )
        delete_success = resp.data and len(resp.data) > 0
        if not delete_success:
            raise HTTPException(status_code=404, detail="Category not found")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

# Endpoint to list keywords for a category (read‑only)
@router.get(
    "/{category_id}/keywords",
    response_model=List[dict],
    summary="List keywords belonging to a category",
)
def list_category_keywords(
    category_id: int = Path(..., description="Category ID", examples=[1])
):
    try:
        resp = (
            supabase.table("keywords")
            .select("word")
            .eq("category_id", category_id)
            .execute()
        )
        return resp.data
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
