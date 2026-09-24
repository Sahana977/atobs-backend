"""REST endpoints for depots  ->  /depots"""
from typing import Optional

from fastapi import APIRouter, Query, Response

from app.api.schemas.depot import DepotCreate, DepotOut, DepotPage, DepotUpdate
from app.services import depot_service as service

router = APIRouter(prefix="/depots", tags=["Depots"])


def _filters(
    depot_code: Optional[str] = None,
    min_capacity: Optional[int] = None,
    max_capacity: Optional[int] = None,
    min_latitude: Optional[float] = None,
    max_latitude: Optional[float] = None,
    min_longitude: Optional[float] = None,
    max_longitude: Optional[float] = None,
    is_active: Optional[bool] = None,
    q: Optional[str] = None,
) -> dict:
    filters = {
        "depot_code": depot_code,
        "min_capacity": min_capacity,
        "max_capacity": max_capacity,
        "min_latitude": min_latitude,
        "max_latitude": max_latitude,
        "min_longitude": min_longitude,
        "max_longitude": max_longitude,
        "is_active": is_active,
        "q": q,
    }
    return {k: v for k, v in filters.items() if v is not None}


@router.get("", response_model=DepotPage, summary="List depots")
def list_depots(
    depot_code: Optional[str] = Query(None, description="exact depot_code"),
    min_capacity: Optional[int] = Query(None, description="minimum capacity"),
    max_capacity: Optional[int] = Query(None, description="maximum capacity"),
    min_latitude: Optional[float] = Query(None, description="minimum latitude"),
    max_latitude: Optional[float] = Query(None, description="maximum latitude"),
    min_longitude: Optional[float] = Query(None, description="minimum longitude"),
    max_longitude: Optional[float] = Query(None, description="maximum longitude"),
    is_active: Optional[bool] = Query(None, description="filter by is_active"),
    q: Optional[str] = Query(None, description="text search in name, area"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    order_by: str = Query("id", description="column to sort by"),
    descending: bool = False,
):
    filters = _filters(depot_code=depot_code, min_capacity=min_capacity, max_capacity=max_capacity, min_latitude=min_latitude, max_latitude=max_latitude, min_longitude=min_longitude, max_longitude=max_longitude, is_active=is_active, q=q)
    return service.list_(filters, limit, offset, order_by, descending)


@router.get("/count", summary="Count depots")
def count_depots(
    depot_code: Optional[str] = Query(None, description="exact depot_code"),
    min_capacity: Optional[int] = Query(None, description="minimum capacity"),
    max_capacity: Optional[int] = Query(None, description="maximum capacity"),
    min_latitude: Optional[float] = Query(None, description="minimum latitude"),
    max_latitude: Optional[float] = Query(None, description="maximum latitude"),
    min_longitude: Optional[float] = Query(None, description="minimum longitude"),
    max_longitude: Optional[float] = Query(None, description="maximum longitude"),
    is_active: Optional[bool] = Query(None, description="filter by is_active"),
    q: Optional[str] = Query(None, description="text search in name, area"),
):
    return {"count": service.count(_filters(depot_code=depot_code, min_capacity=min_capacity, max_capacity=max_capacity, min_latitude=min_latitude, max_latitude=max_latitude, min_longitude=min_longitude, max_longitude=max_longitude, is_active=is_active, q=q))}


@router.get("/export.csv", summary="Download depots as CSV")
def export_depots(
    depot_code: Optional[str] = Query(None, description="exact depot_code"),
    min_capacity: Optional[int] = Query(None, description="minimum capacity"),
    max_capacity: Optional[int] = Query(None, description="maximum capacity"),
    min_latitude: Optional[float] = Query(None, description="minimum latitude"),
    max_latitude: Optional[float] = Query(None, description="maximum latitude"),
    min_longitude: Optional[float] = Query(None, description="minimum longitude"),
    max_longitude: Optional[float] = Query(None, description="maximum longitude"),
    is_active: Optional[bool] = Query(None, description="filter by is_active"),
    q: Optional[str] = Query(None, description="text search in name, area"),
):
    csv_text = service.export_csv(_filters(depot_code=depot_code, min_capacity=min_capacity, max_capacity=max_capacity, min_latitude=min_latitude, max_latitude=max_latitude, min_longitude=min_longitude, max_longitude=max_longitude, is_active=is_active, q=q))
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=depots.csv"},
    )


@router.get("/{item_id}", response_model=DepotOut, summary="Get one")
def get_depot(item_id: int):
    return service.get(item_id).to_dict()


@router.post("", response_model=DepotOut, status_code=201, summary="Create")
def create_depot(payload: DepotCreate):
    return service.create(payload.model_dump()).to_dict()


@router.post("/bulk", response_model=list[DepotOut], status_code=201, summary="Create many (all-or-nothing)")
def bulk_create_depots(payload: list[DepotCreate]):
    return [item.to_dict() for item in service.bulk_create([p.model_dump() for p in payload])]


@router.patch("/{item_id}", response_model=DepotOut, summary="Update some fields")
def update_depot(item_id: int, payload: DepotUpdate):
    return service.update(item_id, payload.model_dump(exclude_unset=True)).to_dict()


@router.delete("/{item_id}", status_code=204, summary="Delete")
def delete_depot(item_id: int):
    service.delete(item_id)
    return Response(status_code=204)
