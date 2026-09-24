"""REST endpoints for users  ->  /users"""
from typing import Optional

from fastapi import APIRouter, Query, Response

from app.api.schemas.app_user import AppUserCreate, AppUserOut, AppUserPage, AppUserUpdate
from app.services import app_user_service as service

router = APIRouter(prefix="/users", tags=["Users"])


def _filters(
    email: Optional[str] = None,
    role: Optional[str] = None,
    home_stop_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    q: Optional[str] = None,
) -> dict:
    filters = {
        "email": email,
        "role": role,
        "home_stop_id": home_stop_id,
        "is_active": is_active,
        "q": q,
    }
    return {k: v for k, v in filters.items() if v is not None}


@router.get("", response_model=AppUserPage, summary="List users")
def list_app_users(
    email: Optional[str] = Query(None, description="exact email"),
    role: Optional[str] = Query(None, description="exact role"),
    home_stop_id: Optional[int] = Query(None, description="exact home_stop_id"),
    is_active: Optional[bool] = Query(None, description="filter by is_active"),
    q: Optional[str] = Query(None, description="text search in full_name"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    order_by: str = Query("id", description="column to sort by"),
    descending: bool = False,
):
    filters = _filters(email=email, role=role, home_stop_id=home_stop_id, is_active=is_active, q=q)
    return service.list_(filters, limit, offset, order_by, descending)


@router.get("/count", summary="Count users")
def count_app_users(
    email: Optional[str] = Query(None, description="exact email"),
    role: Optional[str] = Query(None, description="exact role"),
    home_stop_id: Optional[int] = Query(None, description="exact home_stop_id"),
    is_active: Optional[bool] = Query(None, description="filter by is_active"),
    q: Optional[str] = Query(None, description="text search in full_name"),
):
    return {"count": service.count(_filters(email=email, role=role, home_stop_id=home_stop_id, is_active=is_active, q=q))}


@router.get("/export.csv", summary="Download users as CSV")
def export_app_users(
    email: Optional[str] = Query(None, description="exact email"),
    role: Optional[str] = Query(None, description="exact role"),
    home_stop_id: Optional[int] = Query(None, description="exact home_stop_id"),
    is_active: Optional[bool] = Query(None, description="filter by is_active"),
    q: Optional[str] = Query(None, description="text search in full_name"),
):
    csv_text = service.export_csv(_filters(email=email, role=role, home_stop_id=home_stop_id, is_active=is_active, q=q))
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=app_users.csv"},
    )


@router.get("/{item_id}", response_model=AppUserOut, summary="Get one")
def get_app_user(item_id: int):
    return service.get(item_id).to_dict()


@router.post("", response_model=AppUserOut, status_code=201, summary="Create")
def create_app_user(payload: AppUserCreate):
    return service.create(payload.model_dump()).to_dict()


@router.post("/bulk", response_model=list[AppUserOut], status_code=201, summary="Create many (all-or-nothing)")
def bulk_create_app_users(payload: list[AppUserCreate]):
    return [item.to_dict() for item in service.bulk_create([p.model_dump() for p in payload])]


@router.patch("/{item_id}", response_model=AppUserOut, summary="Update some fields")
def update_app_user(item_id: int, payload: AppUserUpdate):
    return service.update(item_id, payload.model_dump(exclude_unset=True)).to_dict()


@router.delete("/{item_id}", status_code=204, summary="Delete")
def delete_app_user(item_id: int):
    service.delete(item_id)
    return Response(status_code=204)
