"""REST endpoints for buses  ->  /buses"""
from typing import Optional

from fastapi import APIRouter, Query, Response

from app.api.schemas.bus import BusCreate, BusOut, BusPage, BusUpdate
from app.services import bus_service as service

router = APIRouter(prefix="/buses", tags=["Buses"])


def _filters(
    registration_no: Optional[str] = None,
    depot_id: Optional[int] = None,
    min_capacity: Optional[int] = None,
    max_capacity: Optional[int] = None,
    bus_type: Optional[str] = None,
    min_manufacture_year: Optional[int] = None,
    max_manufacture_year: Optional[int] = None,
    is_operational: Optional[bool] = None,
) -> dict:
    filters = {
        "registration_no": registration_no,
        "depot_id": depot_id,
        "min_capacity": min_capacity,
        "max_capacity": max_capacity,
        "bus_type": bus_type,
        "min_manufacture_year": min_manufacture_year,
        "max_manufacture_year": max_manufacture_year,
        "is_operational": is_operational,
    }
    return {k: v for k, v in filters.items() if v is not None}


@router.get("", response_model=BusPage, summary="List buses")
def list_buss(
    registration_no: Optional[str] = Query(None, description="exact registration_no"),
    depot_id: Optional[int] = Query(None, description="exact depot_id"),
    min_capacity: Optional[int] = Query(None, description="minimum capacity"),
    max_capacity: Optional[int] = Query(None, description="maximum capacity"),
    bus_type: Optional[str] = Query(None, description="exact bus_type"),
    min_manufacture_year: Optional[int] = Query(None, description="minimum manufacture_year"),
    max_manufacture_year: Optional[int] = Query(None, description="maximum manufacture_year"),
    is_operational: Optional[bool] = Query(None, description="filter by is_operational"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    order_by: str = Query("id", description="column to sort by"),
    descending: bool = False,
):
    filters = _filters(registration_no=registration_no, depot_id=depot_id, min_capacity=min_capacity, max_capacity=max_capacity, bus_type=bus_type, min_manufacture_year=min_manufacture_year, max_manufacture_year=max_manufacture_year, is_operational=is_operational)
    return service.list_(filters, limit, offset, order_by, descending)


@router.get("/count", summary="Count buses")
def count_buss(
    registration_no: Optional[str] = Query(None, description="exact registration_no"),
    depot_id: Optional[int] = Query(None, description="exact depot_id"),
    min_capacity: Optional[int] = Query(None, description="minimum capacity"),
    max_capacity: Optional[int] = Query(None, description="maximum capacity"),
    bus_type: Optional[str] = Query(None, description="exact bus_type"),
    min_manufacture_year: Optional[int] = Query(None, description="minimum manufacture_year"),
    max_manufacture_year: Optional[int] = Query(None, description="maximum manufacture_year"),
    is_operational: Optional[bool] = Query(None, description="filter by is_operational"),
):
    return {"count": service.count(_filters(registration_no=registration_no, depot_id=depot_id, min_capacity=min_capacity, max_capacity=max_capacity, bus_type=bus_type, min_manufacture_year=min_manufacture_year, max_manufacture_year=max_manufacture_year, is_operational=is_operational))}


@router.get("/export.csv", summary="Download buses as CSV")
def export_buss(
    registration_no: Optional[str] = Query(None, description="exact registration_no"),
    depot_id: Optional[int] = Query(None, description="exact depot_id"),
    min_capacity: Optional[int] = Query(None, description="minimum capacity"),
    max_capacity: Optional[int] = Query(None, description="maximum capacity"),
    bus_type: Optional[str] = Query(None, description="exact bus_type"),
    min_manufacture_year: Optional[int] = Query(None, description="minimum manufacture_year"),
    max_manufacture_year: Optional[int] = Query(None, description="maximum manufacture_year"),
    is_operational: Optional[bool] = Query(None, description="filter by is_operational"),
):
    csv_text = service.export_csv(_filters(registration_no=registration_no, depot_id=depot_id, min_capacity=min_capacity, max_capacity=max_capacity, bus_type=bus_type, min_manufacture_year=min_manufacture_year, max_manufacture_year=max_manufacture_year, is_operational=is_operational))
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=buses.csv"},
    )


@router.get("/{item_id}", response_model=BusOut, summary="Get one")
def get_bus(item_id: int):
    return service.get(item_id).to_dict()


@router.post("", response_model=BusOut, status_code=201, summary="Create")
def create_bus(payload: BusCreate):
    return service.create(payload.model_dump()).to_dict()


@router.post("/bulk", response_model=list[BusOut], status_code=201, summary="Create many (all-or-nothing)")
def bulk_create_buss(payload: list[BusCreate]):
    return [item.to_dict() for item in service.bulk_create([p.model_dump() for p in payload])]


@router.patch("/{item_id}", response_model=BusOut, summary="Update some fields")
def update_bus(item_id: int, payload: BusUpdate):
    return service.update(item_id, payload.model_dump(exclude_unset=True)).to_dict()


@router.delete("/{item_id}", status_code=204, summary="Delete")
def delete_bus(item_id: int):
    service.delete(item_id)
    return Response(status_code=204)
