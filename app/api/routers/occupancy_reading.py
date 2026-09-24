"""REST endpoints for occupancy readings  ->  /occupancy-readings"""
from typing import Optional

from fastapi import APIRouter, Query, Response

from app.api.schemas.occupancy_reading import OccupancyReadingCreate, OccupancyReadingOut, OccupancyReadingPage, OccupancyReadingUpdate
from app.services import occupancy_reading_service as service

router = APIRouter(prefix="/occupancy-readings", tags=["Occupancy Readings"])


def _filters(
    trip_id: Optional[int] = None,
    stop_id: Optional[int] = None,
    recorded_at_from: Optional[str] = None,
    recorded_at_to: Optional[str] = None,
    min_passengers_on_board: Optional[int] = None,
    max_passengers_on_board: Optional[int] = None,
    min_occupancy_pct: Optional[float] = None,
    max_occupancy_pct: Optional[float] = None,
    min_delay_min: Optional[float] = None,
    max_delay_min: Optional[float] = None,
    source: Optional[str] = None,
) -> dict:
    filters = {
        "trip_id": trip_id,
        "stop_id": stop_id,
        "recorded_at_from": recorded_at_from,
        "recorded_at_to": recorded_at_to,
        "min_passengers_on_board": min_passengers_on_board,
        "max_passengers_on_board": max_passengers_on_board,
        "min_occupancy_pct": min_occupancy_pct,
        "max_occupancy_pct": max_occupancy_pct,
        "min_delay_min": min_delay_min,
        "max_delay_min": max_delay_min,
        "source": source,
    }
    return {k: v for k, v in filters.items() if v is not None}


@router.get("", response_model=OccupancyReadingPage, summary="List occupancy readings")
def list_occupancy_readings(
    trip_id: Optional[int] = Query(None, description="exact trip_id"),
    stop_id: Optional[int] = Query(None, description="exact stop_id"),
    recorded_at_from: Optional[str] = Query(None, description="recorded_at on/after (ISO)"),
    recorded_at_to: Optional[str] = Query(None, description="recorded_at on/before (ISO)"),
    min_passengers_on_board: Optional[int] = Query(None, description="minimum passengers_on_board"),
    max_passengers_on_board: Optional[int] = Query(None, description="maximum passengers_on_board"),
    min_occupancy_pct: Optional[float] = Query(None, description="minimum occupancy_pct"),
    max_occupancy_pct: Optional[float] = Query(None, description="maximum occupancy_pct"),
    min_delay_min: Optional[float] = Query(None, description="minimum delay_min"),
    max_delay_min: Optional[float] = Query(None, description="maximum delay_min"),
    source: Optional[str] = Query(None, description="exact source"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    order_by: str = Query("id", description="column to sort by"),
    descending: bool = False,
):
    filters = _filters(trip_id=trip_id, stop_id=stop_id, recorded_at_from=recorded_at_from, recorded_at_to=recorded_at_to, min_passengers_on_board=min_passengers_on_board, max_passengers_on_board=max_passengers_on_board, min_occupancy_pct=min_occupancy_pct, max_occupancy_pct=max_occupancy_pct, min_delay_min=min_delay_min, max_delay_min=max_delay_min, source=source)
    return service.list_(filters, limit, offset, order_by, descending)


@router.get("/count", summary="Count occupancy readings")
def count_occupancy_readings(
    trip_id: Optional[int] = Query(None, description="exact trip_id"),
    stop_id: Optional[int] = Query(None, description="exact stop_id"),
    recorded_at_from: Optional[str] = Query(None, description="recorded_at on/after (ISO)"),
    recorded_at_to: Optional[str] = Query(None, description="recorded_at on/before (ISO)"),
    min_passengers_on_board: Optional[int] = Query(None, description="minimum passengers_on_board"),
    max_passengers_on_board: Optional[int] = Query(None, description="maximum passengers_on_board"),
    min_occupancy_pct: Optional[float] = Query(None, description="minimum occupancy_pct"),
    max_occupancy_pct: Optional[float] = Query(None, description="maximum occupancy_pct"),
    min_delay_min: Optional[float] = Query(None, description="minimum delay_min"),
    max_delay_min: Optional[float] = Query(None, description="maximum delay_min"),
    source: Optional[str] = Query(None, description="exact source"),
):
    return {"count": service.count(_filters(trip_id=trip_id, stop_id=stop_id, recorded_at_from=recorded_at_from, recorded_at_to=recorded_at_to, min_passengers_on_board=min_passengers_on_board, max_passengers_on_board=max_passengers_on_board, min_occupancy_pct=min_occupancy_pct, max_occupancy_pct=max_occupancy_pct, min_delay_min=min_delay_min, max_delay_min=max_delay_min, source=source))}


@router.get("/export.csv", summary="Download occupancy readings as CSV")
def export_occupancy_readings(
    trip_id: Optional[int] = Query(None, description="exact trip_id"),
    stop_id: Optional[int] = Query(None, description="exact stop_id"),
    recorded_at_from: Optional[str] = Query(None, description="recorded_at on/after (ISO)"),
    recorded_at_to: Optional[str] = Query(None, description="recorded_at on/before (ISO)"),
    min_passengers_on_board: Optional[int] = Query(None, description="minimum passengers_on_board"),
    max_passengers_on_board: Optional[int] = Query(None, description="maximum passengers_on_board"),
    min_occupancy_pct: Optional[float] = Query(None, description="minimum occupancy_pct"),
    max_occupancy_pct: Optional[float] = Query(None, description="maximum occupancy_pct"),
    min_delay_min: Optional[float] = Query(None, description="minimum delay_min"),
    max_delay_min: Optional[float] = Query(None, description="maximum delay_min"),
    source: Optional[str] = Query(None, description="exact source"),
):
    csv_text = service.export_csv(_filters(trip_id=trip_id, stop_id=stop_id, recorded_at_from=recorded_at_from, recorded_at_to=recorded_at_to, min_passengers_on_board=min_passengers_on_board, max_passengers_on_board=max_passengers_on_board, min_occupancy_pct=min_occupancy_pct, max_occupancy_pct=max_occupancy_pct, min_delay_min=min_delay_min, max_delay_min=max_delay_min, source=source))
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=occupancy_readings.csv"},
    )


@router.get("/{item_id}", response_model=OccupancyReadingOut, summary="Get one")
def get_occupancy_reading(item_id: int):
    return service.get(item_id).to_dict()


@router.post("", response_model=OccupancyReadingOut, status_code=201, summary="Create")
def create_occupancy_reading(payload: OccupancyReadingCreate):
    return service.create(payload.model_dump()).to_dict()


@router.post("/bulk", response_model=list[OccupancyReadingOut], status_code=201, summary="Create many (all-or-nothing)")
def bulk_create_occupancy_readings(payload: list[OccupancyReadingCreate]):
    return [item.to_dict() for item in service.bulk_create([p.model_dump() for p in payload])]


@router.patch("/{item_id}", response_model=OccupancyReadingOut, summary="Update some fields")
def update_occupancy_reading(item_id: int, payload: OccupancyReadingUpdate):
    return service.update(item_id, payload.model_dump(exclude_unset=True)).to_dict()


@router.delete("/{item_id}", status_code=204, summary="Delete")
def delete_occupancy_reading(item_id: int):
    service.delete(item_id)
    return Response(status_code=204)
