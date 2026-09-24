"""Request/response schemas for occupancy readings."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class OccupancyReadingCreate(BaseModel):
    trip_id: int = Field(..., ge=1)
    stop_id: int = Field(..., ge=1)
    recorded_at: str = ...
    passengers_on_board: int = Field(..., ge=0, le=300)
    occupancy_pct: float = Field(..., ge=0, le=200)
    delay_min: float = Field(0.0, ge=0, le=180)
    source: Literal['apc', 'ticketing', 'manual', 'simulated'] = 'apc'


class OccupancyReadingUpdate(BaseModel):
    """Send only the fields you want to change."""
    trip_id: Optional[int] = Field(None, ge=1)
    stop_id: Optional[int] = Field(None, ge=1)
    recorded_at: Optional[str] = None
    passengers_on_board: Optional[int] = Field(None, ge=0, le=300)
    occupancy_pct: Optional[float] = Field(None, ge=0, le=200)
    delay_min: Optional[float] = Field(None, ge=0, le=180)
    source: Optional[Literal['apc', 'ticketing', 'manual', 'simulated']] = None


class OccupancyReadingOut(BaseModel):
    id: int
    trip_id: Optional[int] = None
    stop_id: Optional[int] = None
    recorded_at: Optional[str] = None
    passengers_on_board: Optional[int] = None
    occupancy_pct: Optional[float] = None
    delay_min: Optional[float] = None
    source: Optional[str] = None
    created_at: str
    updated_at: str


class OccupancyReadingPage(BaseModel):
    items: list[OccupancyReadingOut]
    total: int
    limit: int
    offset: int
