"""REST endpoints for route stops  ->  /route-stops"""
from typing import Optional

from fastapi import APIRouter, Query, Response

from app.api.schemas.route_stop import RouteStopCreate, RouteStopOut, RouteStopPage, RouteStopUpdate
from app.services import route_stop_service as service

router = APIRouter(prefix="/route-stops", tags=["Route Stops"])


def _filters(
    route_id: Optional[int] = None,
    stop_id: Optional[int] = None,
    min_sequence: Optional[int] = None,
    max_sequence: Optional[int] = None,
    min_minutes_from_start: Optional[float] = None,
    max_minutes_from_start: Optional[float] = None,
) -> dict:
    filters = {
        "route_id": route_id,
        "stop_id": stop_id,
        "min_sequence": min_sequence,
        "max_sequence": max_sequence,
        "min_minutes_from_start": min_minutes_from_start,
        "max_minutes_from_start": max_minutes_from_start,
    }
    return {k: v for k, v in filters.items() if v is not None}


@router.get("", response_model=RouteStopPage, summary="List route stops")
def list_route_stops(
    route_id: Optional[int] = Query(None, description="exact route_id"),
    stop_id: Optional[int] = Query(None, description="exact stop_id"),
    min_sequence: Optional[int] = Query(None, description="minimum sequence"),
    max_sequence: Optional[int] = Query(None, description="maximum sequence"),
    min_minutes_from_start: Optional[float] = Query(None, description="minimum minutes_from_start"),
    max_minutes_from_start: Optional[float] = Query(None, description="maximum minutes_from_start"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    order_by: str = Query("id", description="column to sort by"),
    descending: bool = False,
):
    filters = _filters(route_id=route_id, stop_id=stop_id, min_sequence=min_sequence, max_sequence=max_sequence, min_minutes_from_start=min_minutes_from_start, max_minutes_from_start=max_minutes_from_start)
    return service.list_(filters, limit, offset, order_by, descending)


@router.get("/count", summary="Count route stops")
def count_route_stops(
    route_id: Optional[int] = Query(None, description="exact route_id"),
    stop_id: Optional[int] = Query(None, description="exact stop_id"),
    min_sequence: Optional[int] = Query(None, description="minimum sequence"),
    max_sequence: Optional[int] = Query(None, description="maximum sequence"),
    min_minutes_from_start: Optional[float] = Query(None, description="minimum minutes_from_start"),
    max_minutes_from_start: Optional[float] = Query(None, description="maximum minutes_from_start"),
):
    return {"count": service.count(_filters(route_id=route_id, stop_id=stop_id, min_sequence=min_sequence, max_sequence=max_sequence, min_minutes_from_start=min_minutes_from_start, max_minutes_from_start=max_minutes_from_start))}


@router.get("/export.csv", summary="Download route stops as CSV")
def export_route_stops(
    route_id: Optional[int] = Query(None, description="exact route_id"),
    stop_id: Optional[int] = Query(None, description="exact stop_id"),
    min_sequence: Optional[int] = Query(None, description="minimum sequence"),
    max_sequence: Optional[int] = Query(None, description="maximum sequence"),
    min_minutes_from_start: Optional[float] = Query(None, description="minimum minutes_from_start"),
    max_minutes_from_start: Optional[float] = Query(None, description="maximum minutes_from_start"),
):
    csv_text = service.export_csv(_filters(route_id=route_id, stop_id=stop_id, min_sequence=min_sequence, max_sequence=max_sequence, min_minutes_from_start=min_minutes_from_start, max_minutes_from_start=max_minutes_from_start))
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=route_stops.csv"},
    )


@router.get("/{item_id}", response_model=RouteStopOut, summary="Get one")
def get_route_stop(item_id: int):
    return service.get(item_id).to_dict()


@router.post("", response_model=RouteStopOut, status_code=201, summary="Create")
def create_route_stop(payload: RouteStopCreate):
    return service.create(payload.model_dump()).to_dict()


@router.post("/bulk", response_model=list[RouteStopOut], status_code=201, summary="Create many (all-or-nothing)")
def bulk_create_route_stops(payload: list[RouteStopCreate]):
    return [item.to_dict() for item in service.bulk_create([p.model_dump() for p in payload])]


@router.patch("/{item_id}", response_model=RouteStopOut, summary="Update some fields")
def update_route_stop(item_id: int, payload: RouteStopUpdate):
    return service.update(item_id, payload.model_dump(exclude_unset=True)).to_dict()


@router.delete("/{item_id}", status_code=204, summary="Delete")
def delete_route_stop(item_id: int):
    service.delete(item_id)
    return Response(status_code=204)
