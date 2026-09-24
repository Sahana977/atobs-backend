"""REST endpoints for traffic readings  ->  /traffic-readings"""
from typing import Optional

from fastapi import APIRouter, Query, Response

from app.api.schemas.traffic_reading import TrafficReadingCreate, TrafficReadingOut, TrafficReadingPage, TrafficReadingUpdate
from app.services import traffic_reading_service as service

router = APIRouter(prefix="/traffic-readings", tags=["Traffic Readings"])


def _filters(
    stop_id: Optional[int] = None,
    recorded_at_from: Optional[str] = None,
    recorded_at_to: Optional[str] = None,
    traffic_level: Optional[str] = None,
    min_vehicle_density: Optional[float] = None,
    max_vehicle_density: Optional[float] = None,
    min_avg_speed: Optional[float] = None,
    max_avg_speed: Optional[float] = None,
    min_road_occupancy: Optional[float] = None,
    max_road_occupancy: Optional[float] = None,
    min_traffic_flow: Optional[float] = None,
    max_traffic_flow: Optional[float] = None,
    source: Optional[str] = None,
) -> dict:
    filters = {
        "stop_id": stop_id,
        "recorded_at_from": recorded_at_from,
        "recorded_at_to": recorded_at_to,
        "traffic_level": traffic_level,
        "min_vehicle_density": min_vehicle_density,
        "max_vehicle_density": max_vehicle_density,
        "min_avg_speed": min_avg_speed,
        "max_avg_speed": max_avg_speed,
        "min_road_occupancy": min_road_occupancy,
        "max_road_occupancy": max_road_occupancy,
        "min_traffic_flow": min_traffic_flow,
        "max_traffic_flow": max_traffic_flow,
        "source": source,
    }
    return {k: v for k, v in filters.items() if v is not None}


@router.get("", response_model=TrafficReadingPage, summary="List traffic readings")
def list_traffic_readings(
    stop_id: Optional[int] = Query(None, description="exact stop_id"),
    recorded_at_from: Optional[str] = Query(None, description="recorded_at on/after (ISO)"),
    recorded_at_to: Optional[str] = Query(None, description="recorded_at on/before (ISO)"),
    traffic_level: Optional[str] = Query(None, description="exact traffic_level"),
    min_vehicle_density: Optional[float] = Query(None, description="minimum vehicle_density"),
    max_vehicle_density: Optional[float] = Query(None, description="maximum vehicle_density"),
    min_avg_speed: Optional[float] = Query(None, description="minimum avg_speed"),
    max_avg_speed: Optional[float] = Query(None, description="maximum avg_speed"),
    min_road_occupancy: Optional[float] = Query(None, description="minimum road_occupancy"),
    max_road_occupancy: Optional[float] = Query(None, description="maximum road_occupancy"),
    min_traffic_flow: Optional[float] = Query(None, description="minimum traffic_flow"),
    max_traffic_flow: Optional[float] = Query(None, description="maximum traffic_flow"),
    source: Optional[str] = Query(None, description="exact source"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    order_by: str = Query("id", description="column to sort by"),
    descending: bool = False,
):
    filters = _filters(stop_id=stop_id, recorded_at_from=recorded_at_from, recorded_at_to=recorded_at_to, traffic_level=traffic_level, min_vehicle_density=min_vehicle_density, max_vehicle_density=max_vehicle_density, min_avg_speed=min_avg_speed, max_avg_speed=max_avg_speed, min_road_occupancy=min_road_occupancy, max_road_occupancy=max_road_occupancy, min_traffic_flow=min_traffic_flow, max_traffic_flow=max_traffic_flow, source=source)
    return service.list_(filters, limit, offset, order_by, descending)


@router.get("/count", summary="Count traffic readings")
def count_traffic_readings(
    stop_id: Optional[int] = Query(None, description="exact stop_id"),
    recorded_at_from: Optional[str] = Query(None, description="recorded_at on/after (ISO)"),
    recorded_at_to: Optional[str] = Query(None, description="recorded_at on/before (ISO)"),
    traffic_level: Optional[str] = Query(None, description="exact traffic_level"),
    min_vehicle_density: Optional[float] = Query(None, description="minimum vehicle_density"),
    max_vehicle_density: Optional[float] = Query(None, description="maximum vehicle_density"),
    min_avg_speed: Optional[float] = Query(None, description="minimum avg_speed"),
    max_avg_speed: Optional[float] = Query(None, description="maximum avg_speed"),
    min_road_occupancy: Optional[float] = Query(None, description="minimum road_occupancy"),
    max_road_occupancy: Optional[float] = Query(None, description="maximum road_occupancy"),
    min_traffic_flow: Optional[float] = Query(None, description="minimum traffic_flow"),
    max_traffic_flow: Optional[float] = Query(None, description="maximum traffic_flow"),
    source: Optional[str] = Query(None, description="exact source"),
):
    return {"count": service.count(_filters(stop_id=stop_id, recorded_at_from=recorded_at_from, recorded_at_to=recorded_at_to, traffic_level=traffic_level, min_vehicle_density=min_vehicle_density, max_vehicle_density=max_vehicle_density, min_avg_speed=min_avg_speed, max_avg_speed=max_avg_speed, min_road_occupancy=min_road_occupancy, max_road_occupancy=max_road_occupancy, min_traffic_flow=min_traffic_flow, max_traffic_flow=max_traffic_flow, source=source))}


@router.get("/export.csv", summary="Download traffic readings as CSV")
def export_traffic_readings(
    stop_id: Optional[int] = Query(None, description="exact stop_id"),
    recorded_at_from: Optional[str] = Query(None, description="recorded_at on/after (ISO)"),
    recorded_at_to: Optional[str] = Query(None, description="recorded_at on/before (ISO)"),
    traffic_level: Optional[str] = Query(None, description="exact traffic_level"),
    min_vehicle_density: Optional[float] = Query(None, description="minimum vehicle_density"),
    max_vehicle_density: Optional[float] = Query(None, description="maximum vehicle_density"),
    min_avg_speed: Optional[float] = Query(None, description="minimum avg_speed"),
    max_avg_speed: Optional[float] = Query(None, description="maximum avg_speed"),
    min_road_occupancy: Optional[float] = Query(None, description="minimum road_occupancy"),
    max_road_occupancy: Optional[float] = Query(None, description="maximum road_occupancy"),
    min_traffic_flow: Optional[float] = Query(None, description="minimum traffic_flow"),
    max_traffic_flow: Optional[float] = Query(None, description="maximum traffic_flow"),
    source: Optional[str] = Query(None, description="exact source"),
):
    csv_text = service.export_csv(_filters(stop_id=stop_id, recorded_at_from=recorded_at_from, recorded_at_to=recorded_at_to, traffic_level=traffic_level, min_vehicle_density=min_vehicle_density, max_vehicle_density=max_vehicle_density, min_avg_speed=min_avg_speed, max_avg_speed=max_avg_speed, min_road_occupancy=min_road_occupancy, max_road_occupancy=max_road_occupancy, min_traffic_flow=min_traffic_flow, max_traffic_flow=max_traffic_flow, source=source))
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=traffic_readings.csv"},
    )


@router.get("/{item_id}", response_model=TrafficReadingOut, summary="Get one")
def get_traffic_reading(item_id: int):
    return service.get(item_id).to_dict()


@router.post("", response_model=TrafficReadingOut, status_code=201, summary="Create")
def create_traffic_reading(payload: TrafficReadingCreate):
    return service.create(payload.model_dump()).to_dict()


@router.post("/bulk", response_model=list[TrafficReadingOut], status_code=201, summary="Create many (all-or-nothing)")
def bulk_create_traffic_readings(payload: list[TrafficReadingCreate]):
    return [item.to_dict() for item in service.bulk_create([p.model_dump() for p in payload])]


@router.patch("/{item_id}", response_model=TrafficReadingOut, summary="Update some fields")
def update_traffic_reading(item_id: int, payload: TrafficReadingUpdate):
    return service.update(item_id, payload.model_dump(exclude_unset=True)).to_dict()


@router.delete("/{item_id}", status_code=204, summary="Delete")
def delete_traffic_reading(item_id: int):
    service.delete(item_id)
    return Response(status_code=204)
