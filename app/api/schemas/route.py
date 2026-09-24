"""Request/response schemas for routes."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class RouteCreate(BaseModel):
    route_number: str = Field(..., max_length=20)
    name: str = Field(..., max_length=200)
    origin_stop_id: int = Field(..., ge=1)
    destination_stop_id: int = Field(..., ge=1)
    distance_km: float = Field(..., ge=0.1, le=200)
    service_type: Literal['ordinary', 'vajra', 'vayu_vajra', 'metro_feeder'] = 'ordinary'
    avg_headway_min: int = Field(15, ge=1, le=180)
    is_active: bool = True


class RouteUpdate(BaseModel):
    """Send only the fields you want to change."""
    route_number: Optional[str] = Field(None, max_length=20)
    name: Optional[str] = Field(None, max_length=200)
    origin_stop_id: Optional[int] = Field(None, ge=1)
    destination_stop_id: Optional[int] = Field(None, ge=1)
    distance_km: Optional[float] = Field(None, ge=0.1, le=200)
    service_type: Optional[Literal['ordinary', 'vajra', 'vayu_vajra', 'metro_feeder']] = None
    avg_headway_min: Optional[int] = Field(None, ge=1, le=180)
    is_active: Optional[bool] = None


class RouteOut(BaseModel):
    id: int
    route_number: Optional[str] = None
    name: Optional[str] = None
    origin_stop_id: Optional[int] = None
    destination_stop_id: Optional[int] = None
    distance_km: Optional[float] = None
    service_type: Optional[str] = None
    avg_headway_min: Optional[int] = None
    is_active: Optional[bool] = None
    created_at: str
    updated_at: str


class RoutePage(BaseModel):
    items: list[RouteOut]
    total: int
    limit: int
    offset: int
