"""Request/response schemas for trips."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class TripCreate(BaseModel):
    trip_code: str = Field(..., max_length=30)
    route_id: int = Field(..., ge=1)
    bus_id: int = Field(..., ge=1)
    scheduled_start: str = ...
    scheduled_end: Optional[str] = None
    status: Literal['scheduled', 'running', 'completed', 'cancelled'] = 'scheduled'


class TripUpdate(BaseModel):
    """Send only the fields you want to change."""
    trip_code: Optional[str] = Field(None, max_length=30)
    route_id: Optional[int] = Field(None, ge=1)
    bus_id: Optional[int] = Field(None, ge=1)
    scheduled_start: Optional[str] = None
    scheduled_end: Optional[str] = None
    status: Optional[Literal['scheduled', 'running', 'completed', 'cancelled']] = None


class TripOut(BaseModel):
    id: int
    trip_code: Optional[str] = None
    route_id: Optional[int] = None
    bus_id: Optional[int] = None
    scheduled_start: Optional[str] = None
    scheduled_end: Optional[str] = None
    status: Optional[str] = None
    created_at: str
    updated_at: str


class TripPage(BaseModel):
    items: list[TripOut]
    total: int
    limit: int
    offset: int
