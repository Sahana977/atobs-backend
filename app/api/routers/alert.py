"""REST endpoints for alerts  ->  /alerts"""
from typing import Optional

from fastapi import APIRouter, Query, Response

from app.api.schemas.alert import AlertCreate, AlertOut, AlertPage, AlertUpdate
from app.services import alert_service as service

router = APIRouter(prefix="/alerts", tags=["Alerts"])


def _filters(
    severity: Optional[str] = None,
    stop_id: Optional[int] = None,
    route_id: Optional[int] = None,
    starts_at_from: Optional[str] = None,
    starts_at_to: Optional[str] = None,
    ends_at_from: Optional[str] = None,
    ends_at_to: Optional[str] = None,
    is_active: Optional[bool] = None,
    q: Optional[str] = None,
) -> dict:
    filters = {
        "severity": severity,
        "stop_id": stop_id,
        "route_id": route_id,
        "starts_at_from": starts_at_from,
        "starts_at_to": starts_at_to,
        "ends_at_from": ends_at_from,
        "ends_at_to": ends_at_to,
        "is_active": is_active,
        "q": q,
    }
    return {k: v for k, v in filters.items() if v is not None}


@router.get("", response_model=AlertPage, summary="List alerts")
def list_alerts(
    severity: Optional[str] = Query(None, description="exact severity"),
    stop_id: Optional[int] = Query(None, description="exact stop_id"),
    route_id: Optional[int] = Query(None, description="exact route_id"),
    starts_at_from: Optional[str] = Query(None, description="starts_at on/after (ISO)"),
    starts_at_to: Optional[str] = Query(None, description="starts_at on/before (ISO)"),
    ends_at_from: Optional[str] = Query(None, description="ends_at on/after (ISO)"),
    ends_at_to: Optional[str] = Query(None, description="ends_at on/before (ISO)"),
    is_active: Optional[bool] = Query(None, description="filter by is_active"),
    q: Optional[str] = Query(None, description="text search in title, message"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    order_by: str = Query("id", description="column to sort by"),
    descending: bool = False,
):
    filters = _filters(severity=severity, stop_id=stop_id, route_id=route_id, starts_at_from=starts_at_from, starts_at_to=starts_at_to, ends_at_from=ends_at_from, ends_at_to=ends_at_to, is_active=is_active, q=q)
    return service.list_(filters, limit, offset, order_by, descending)


@router.get("/count", summary="Count alerts")
def count_alerts(
    severity: Optional[str] = Query(None, description="exact severity"),
    stop_id: Optional[int] = Query(None, description="exact stop_id"),
    route_id: Optional[int] = Query(None, description="exact route_id"),
    starts_at_from: Optional[str] = Query(None, description="starts_at on/after (ISO)"),
    starts_at_to: Optional[str] = Query(None, description="starts_at on/before (ISO)"),
    ends_at_from: Optional[str] = Query(None, description="ends_at on/after (ISO)"),
    ends_at_to: Optional[str] = Query(None, description="ends_at on/before (ISO)"),
    is_active: Optional[bool] = Query(None, description="filter by is_active"),
    q: Optional[str] = Query(None, description="text search in title, message"),
):
    return {"count": service.count(_filters(severity=severity, stop_id=stop_id, route_id=route_id, starts_at_from=starts_at_from, starts_at_to=starts_at_to, ends_at_from=ends_at_from, ends_at_to=ends_at_to, is_active=is_active, q=q))}


@router.get("/export.csv", summary="Download alerts as CSV")
def export_alerts(
    severity: Optional[str] = Query(None, description="exact severity"),
    stop_id: Optional[int] = Query(None, description="exact stop_id"),
    route_id: Optional[int] = Query(None, description="exact route_id"),
    starts_at_from: Optional[str] = Query(None, description="starts_at on/after (ISO)"),
    starts_at_to: Optional[str] = Query(None, description="starts_at on/before (ISO)"),
    ends_at_from: Optional[str] = Query(None, description="ends_at on/after (ISO)"),
    ends_at_to: Optional[str] = Query(None, description="ends_at on/before (ISO)"),
    is_active: Optional[bool] = Query(None, description="filter by is_active"),
    q: Optional[str] = Query(None, description="text search in title, message"),
):
    csv_text = service.export_csv(_filters(severity=severity, stop_id=stop_id, route_id=route_id, starts_at_from=starts_at_from, starts_at_to=starts_at_to, ends_at_from=ends_at_from, ends_at_to=ends_at_to, is_active=is_active, q=q))
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=alerts.csv"},
    )


@router.get("/{item_id}", response_model=AlertOut, summary="Get one")
def get_alert(item_id: int):
    return service.get(item_id).to_dict()


@router.post("", response_model=AlertOut, status_code=201, summary="Create")
def create_alert(payload: AlertCreate):
    return service.create(payload.model_dump()).to_dict()


@router.post("/bulk", response_model=list[AlertOut], status_code=201, summary="Create many (all-or-nothing)")
def bulk_create_alerts(payload: list[AlertCreate]):
    return [item.to_dict() for item in service.bulk_create([p.model_dump() for p in payload])]


@router.patch("/{item_id}", response_model=AlertOut, summary="Update some fields")
def update_alert(item_id: int, payload: AlertUpdate):
    return service.update(item_id, payload.model_dump(exclude_unset=True)).to_dict()


@router.delete("/{item_id}", status_code=204, summary="Delete")
def delete_alert(item_id: int):
    service.delete(item_id)
    return Response(status_code=204)
