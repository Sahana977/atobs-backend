"""REST endpoints for routes  ->  /routes"""
from typing import Optional

from fastapi import APIRouter, Query, Response

from app.api.schemas.route import RouteCreate, RouteOut, RoutePage, RouteUpdate
from app.services import route_service as service

router = APIRouter(prefix="/routes", tags=["Routes"])


def _filters(
    route_number: Optional[str] = None,
    origin_stop_id: Optional[int] = None,
    destination_stop_id: Optional[int] = None,
    min_distance_km: Optional[float] = None,
    max_distance_km: Optional[float] = None,
    service_type: Optional[str] = None,
    min_avg_headway_min: Optional[int] = None,
    max_avg_headway_min: Optional[int] = None,
    is_active: Optional[bool] = None,
    q: Optional[str] = None,
) -> dict:
    filters = {
        "route_number": route_number,
        "origin_stop_id": origin_stop_id,
        "destination_stop_id": destination_stop_id,
        "min_distance_km": min_distance_km,
        "max_distance_km": max_distance_km,
        "service_type": service_type,
        "min_avg_headway_min": min_avg_headway_min,
        "max_avg_headway_min": max_avg_headway_min,
        "is_active": is_active,
        "q": q,
    }
    return {k: v for k, v in filters.items() if v is not None}


@router.get("", response_model=RoutePage, summary="List routes")
def list_routes(
    route_number: Optional[str] = Query(None, description="exact route_number"),
    origin_stop_id: Optional[int] = Query(None, description="exact origin_stop_id"),
    destination_stop_id: Optional[int] = Query(None, description="exact destination_stop_id"),
    min_distance_km: Optional[float] = Query(None, description="minimum distance_km"),
    max_distance_km: Optional[float] = Query(None, description="maximum distance_km"),
    service_type: Optional[str] = Query(None, description="exact service_type"),
    min_avg_headway_min: Optional[int] = Query(None, description="minimum avg_headway_min"),
    max_avg_headway_min: Optional[int] = Query(None, description="maximum avg_headway_min"),
    is_active: Optional[bool] = Query(None, description="filter by is_active"),
    q: Optional[str] = Query(None, description="text search in name"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    order_by: str = Query("id", description="column to sort by"),
    descending: bool = False,
):
    filters = _filters(route_number=route_number, origin_stop_id=origin_stop_id, destination_stop_id=destination_stop_id, min_distance_km=min_distance_km, max_distance_km=max_distance_km, service_type=service_type, min_avg_headway_min=min_avg_headway_min, max_avg_headway_min=max_avg_headway_min, is_active=is_active, q=q)
    return service.list_(filters, limit, offset, order_by, descending)


@router.get("/count", summary="Count routes")
def count_routes(
    route_number: Optional[str] = Query(None, description="exact route_number"),
    origin_stop_id: Optional[int] = Query(None, description="exact origin_stop_id"),
    destination_stop_id: Optional[int] = Query(None, description="exact destination_stop_id"),
    min_distance_km: Optional[float] = Query(None, description="minimum distance_km"),
    max_distance_km: Optional[float] = Query(None, description="maximum distance_km"),
    service_type: Optional[str] = Query(None, description="exact service_type"),
    min_avg_headway_min: Optional[int] = Query(None, description="minimum avg_headway_min"),
    max_avg_headway_min: Optional[int] = Query(None, description="maximum avg_headway_min"),
    is_active: Optional[bool] = Query(None, description="filter by is_active"),
    q: Optional[str] = Query(None, description="text search in name"),
):
    return {"count": service.count(_filters(route_number=route_number, origin_stop_id=origin_stop_id, destination_stop_id=destination_stop_id, min_distance_km=min_distance_km, max_distance_km=max_distance_km, service_type=service_type, min_avg_headway_min=min_avg_headway_min, max_avg_headway_min=max_avg_headway_min, is_active=is_active, q=q))}


@router.get("/export.csv", summary="Download routes as CSV")
def export_routes(
    route_number: Optional[str] = Query(None, description="exact route_number"),
    origin_stop_id: Optional[int] = Query(None, description="exact origin_stop_id"),
    destination_stop_id: Optional[int] = Query(None, description="exact destination_stop_id"),
    min_distance_km: Optional[float] = Query(None, description="minimum distance_km"),
    max_distance_km: Optional[float] = Query(None, description="maximum distance_km"),
    service_type: Optional[str] = Query(None, description="exact service_type"),
    min_avg_headway_min: Optional[int] = Query(None, description="minimum avg_headway_min"),
    max_avg_headway_min: Optional[int] = Query(None, description="maximum avg_headway_min"),
    is_active: Optional[bool] = Query(None, description="filter by is_active"),
    q: Optional[str] = Query(None, description="text search in name"),
):
    csv_text = service.export_csv(_filters(route_number=route_number, origin_stop_id=origin_stop_id, destination_stop_id=destination_stop_id, min_distance_km=min_distance_km, max_distance_km=max_distance_km, service_type=service_type, min_avg_headway_min=min_avg_headway_min, max_avg_headway_min=max_avg_headway_min, is_active=is_active, q=q))
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=routes.csv"},
    )


@router.get("/{item_id}", response_model=RouteOut, summary="Get one")
def get_route(item_id: int):
    return service.get(item_id).to_dict()


@router.post("", response_model=RouteOut, status_code=201, summary="Create")
def create_route(payload: RouteCreate):
    return service.create(payload.model_dump()).to_dict()


@router.post("/bulk", response_model=list[RouteOut], status_code=201, summary="Create many (all-or-nothing)")
def bulk_create_routes(payload: list[RouteCreate]):
    return [item.to_dict() for item in service.bulk_create([p.model_dump() for p in payload])]


@router.patch("/{item_id}", response_model=RouteOut, summary="Update some fields")
def update_route(item_id: int, payload: RouteUpdate):
    return service.update(item_id, payload.model_dump(exclude_unset=True)).to_dict()


@router.delete("/{item_id}", status_code=204, summary="Delete")
def delete_route(item_id: int):
    service.delete(item_id)
    return Response(status_code=204)
