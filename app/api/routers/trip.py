"""REST endpoints for trips  ->  /trips"""
from typing import Optional

from fastapi import APIRouter, Query, Response

from app.api.schemas.trip import TripCreate, TripOut, TripPage, TripUpdate
from app.services import trip_service as service

router = APIRouter(prefix="/trips", tags=["Trips"])


def _filters(
    trip_code: Optional[str] = None,
    route_id: Optional[int] = None,
    bus_id: Optional[int] = None,
    scheduled_start_from: Optional[str] = None,
    scheduled_start_to: Optional[str] = None,
    scheduled_end_from: Optional[str] = None,
    scheduled_end_to: Optional[str] = None,
    status: Optional[str] = None,
) -> dict:
    filters = {
        "trip_code": trip_code,
        "route_id": route_id,
        "bus_id": bus_id,
        "scheduled_start_from": scheduled_start_from,
        "scheduled_start_to": scheduled_start_to,
        "scheduled_end_from": scheduled_end_from,
        "scheduled_end_to": scheduled_end_to,
        "status": status,
    }
    return {k: v for k, v in filters.items() if v is not None}


@router.get("", response_model=TripPage, summary="List trips")
def list_trips(
    trip_code: Optional[str] = Query(None, description="exact trip_code"),
    route_id: Optional[int] = Query(None, description="exact route_id"),
    bus_id: Optional[int] = Query(None, description="exact bus_id"),
    scheduled_start_from: Optional[str] = Query(None, description="scheduled_start on/after (ISO)"),
    scheduled_start_to: Optional[str] = Query(None, description="scheduled_start on/before (ISO)"),
    scheduled_end_from: Optional[str] = Query(None, description="scheduled_end on/after (ISO)"),
    scheduled_end_to: Optional[str] = Query(None, description="scheduled_end on/before (ISO)"),
    status: Optional[str] = Query(None, description="exact status"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    order_by: str = Query("id", description="column to sort by"),
    descending: bool = False,
):
    filters = _filters(trip_code=trip_code, route_id=route_id, bus_id=bus_id, scheduled_start_from=scheduled_start_from, scheduled_start_to=scheduled_start_to, scheduled_end_from=scheduled_end_from, scheduled_end_to=scheduled_end_to, status=status)
    return service.list_(filters, limit, offset, order_by, descending)


@router.get("/count", summary="Count trips")
def count_trips(
    trip_code: Optional[str] = Query(None, description="exact trip_code"),
    route_id: Optional[int] = Query(None, description="exact route_id"),
    bus_id: Optional[int] = Query(None, description="exact bus_id"),
    scheduled_start_from: Optional[str] = Query(None, description="scheduled_start on/after (ISO)"),
    scheduled_start_to: Optional[str] = Query(None, description="scheduled_start on/before (ISO)"),
    scheduled_end_from: Optional[str] = Query(None, description="scheduled_end on/after (ISO)"),
    scheduled_end_to: Optional[str] = Query(None, description="scheduled_end on/before (ISO)"),
    status: Optional[str] = Query(None, description="exact status"),
):
    return {"count": service.count(_filters(trip_code=trip_code, route_id=route_id, bus_id=bus_id, scheduled_start_from=scheduled_start_from, scheduled_start_to=scheduled_start_to, scheduled_end_from=scheduled_end_from, scheduled_end_to=scheduled_end_to, status=status))}


@router.get("/export.csv", summary="Download trips as CSV")
def export_trips(
    trip_code: Optional[str] = Query(None, description="exact trip_code"),
    route_id: Optional[int] = Query(None, description="exact route_id"),
    bus_id: Optional[int] = Query(None, description="exact bus_id"),
    scheduled_start_from: Optional[str] = Query(None, description="scheduled_start on/after (ISO)"),
    scheduled_start_to: Optional[str] = Query(None, description="scheduled_start on/before (ISO)"),
    scheduled_end_from: Optional[str] = Query(None, description="scheduled_end on/after (ISO)"),
    scheduled_end_to: Optional[str] = Query(None, description="scheduled_end on/before (ISO)"),
    status: Optional[str] = Query(None, description="exact status"),
):
    csv_text = service.export_csv(_filters(trip_code=trip_code, route_id=route_id, bus_id=bus_id, scheduled_start_from=scheduled_start_from, scheduled_start_to=scheduled_start_to, scheduled_end_from=scheduled_end_from, scheduled_end_to=scheduled_end_to, status=status))
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=trips.csv"},
    )


@router.get("/{item_id}", response_model=TripOut, summary="Get one")
def get_trip(item_id: int):
    return service.get(item_id).to_dict()


@router.post("", response_model=TripOut, status_code=201, summary="Create")
def create_trip(payload: TripCreate):
    return service.create(payload.model_dump()).to_dict()


@router.post("/bulk", response_model=list[TripOut], status_code=201, summary="Create many (all-or-nothing)")
def bulk_create_trips(payload: list[TripCreate]):
    return [item.to_dict() for item in service.bulk_create([p.model_dump() for p in payload])]


@router.patch("/{item_id}", response_model=TripOut, summary="Update some fields")
def update_trip(item_id: int, payload: TripUpdate):
    return service.update(item_id, payload.model_dump(exclude_unset=True)).to_dict()


@router.delete("/{item_id}", status_code=204, summary="Delete")
def delete_trip(item_id: int):
    service.delete(item_id)
    return Response(status_code=204)
