"""REST endpoints for stops  ->  /stops"""
from typing import Optional

from fastapi import APIRouter, Query, Response

from app.api.schemas.stop import StopCreate, StopOut, StopPage, StopUpdate
from app.services import stop_service as service

router = APIRouter(prefix="/stops", tags=["Stops"])


def _filters(
    stop_code: Optional[str] = None,
    min_latitude: Optional[float] = None,
    max_latitude: Optional[float] = None,
    min_longitude: Optional[float] = None,
    max_longitude: Optional[float] = None,
    zone: Optional[str] = None,
    has_shelter: Optional[bool] = None,
    is_accessible: Optional[bool] = None,
    q: Optional[str] = None,
) -> dict:
    filters = {
        "stop_code": stop_code,
        "min_latitude": min_latitude,
        "max_latitude": max_latitude,
        "min_longitude": min_longitude,
        "max_longitude": max_longitude,
        "zone": zone,
        "has_shelter": has_shelter,
        "is_accessible": is_accessible,
        "q": q,
    }
    return {k: v for k, v in filters.items() if v is not None}


@router.get("", response_model=StopPage, summary="List stops")
def list_stops(
    stop_code: Optional[str] = Query(None, description="exact stop_code"),
    min_latitude: Optional[float] = Query(None, description="minimum latitude"),
    max_latitude: Optional[float] = Query(None, description="maximum latitude"),
    min_longitude: Optional[float] = Query(None, description="minimum longitude"),
    max_longitude: Optional[float] = Query(None, description="maximum longitude"),
    zone: Optional[str] = Query(None, description="exact zone"),
    has_shelter: Optional[bool] = Query(None, description="filter by has_shelter"),
    is_accessible: Optional[bool] = Query(None, description="filter by is_accessible"),
    q: Optional[str] = Query(None, description="text search in name, area"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    order_by: str = Query("id", description="column to sort by"),
    descending: bool = False,
):
    filters = _filters(stop_code=stop_code, min_latitude=min_latitude, max_latitude=max_latitude, min_longitude=min_longitude, max_longitude=max_longitude, zone=zone, has_shelter=has_shelter, is_accessible=is_accessible, q=q)
    return service.list_(filters, limit, offset, order_by, descending)


@router.get("/count", summary="Count stops")
def count_stops(
    stop_code: Optional[str] = Query(None, description="exact stop_code"),
    min_latitude: Optional[float] = Query(None, description="minimum latitude"),
    max_latitude: Optional[float] = Query(None, description="maximum latitude"),
    min_longitude: Optional[float] = Query(None, description="minimum longitude"),
    max_longitude: Optional[float] = Query(None, description="maximum longitude"),
    zone: Optional[str] = Query(None, description="exact zone"),
    has_shelter: Optional[bool] = Query(None, description="filter by has_shelter"),
    is_accessible: Optional[bool] = Query(None, description="filter by is_accessible"),
    q: Optional[str] = Query(None, description="text search in name, area"),
):
    return {"count": service.count(_filters(stop_code=stop_code, min_latitude=min_latitude, max_latitude=max_latitude, min_longitude=min_longitude, max_longitude=max_longitude, zone=zone, has_shelter=has_shelter, is_accessible=is_accessible, q=q))}


@router.get("/export.csv", summary="Download stops as CSV")
def export_stops(
    stop_code: Optional[str] = Query(None, description="exact stop_code"),
    min_latitude: Optional[float] = Query(None, description="minimum latitude"),
    max_latitude: Optional[float] = Query(None, description="maximum latitude"),
    min_longitude: Optional[float] = Query(None, description="minimum longitude"),
    max_longitude: Optional[float] = Query(None, description="maximum longitude"),
    zone: Optional[str] = Query(None, description="exact zone"),
    has_shelter: Optional[bool] = Query(None, description="filter by has_shelter"),
    is_accessible: Optional[bool] = Query(None, description="filter by is_accessible"),
    q: Optional[str] = Query(None, description="text search in name, area"),
):
    csv_text = service.export_csv(_filters(stop_code=stop_code, min_latitude=min_latitude, max_latitude=max_latitude, min_longitude=min_longitude, max_longitude=max_longitude, zone=zone, has_shelter=has_shelter, is_accessible=is_accessible, q=q))
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=stops.csv"},
    )


@router.get("/{item_id}", response_model=StopOut, summary="Get one")
def get_stop(item_id: int):
    return service.get(item_id).to_dict()


@router.post("", response_model=StopOut, status_code=201, summary="Create")
def create_stop(payload: StopCreate):
    return service.create(payload.model_dump()).to_dict()


@router.post("/bulk", response_model=list[StopOut], status_code=201, summary="Create many (all-or-nothing)")
def bulk_create_stops(payload: list[StopCreate]):
    return [item.to_dict() for item in service.bulk_create([p.model_dump() for p in payload])]


@router.patch("/{item_id}", response_model=StopOut, summary="Update some fields")
def update_stop(item_id: int, payload: StopUpdate):
    return service.update(item_id, payload.model_dump(exclude_unset=True)).to_dict()


@router.delete("/{item_id}", status_code=204, summary="Delete")
def delete_stop(item_id: int):
    service.delete(item_id)
    return Response(status_code=204)
