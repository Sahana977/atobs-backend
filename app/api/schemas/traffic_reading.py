"""Request/response schemas for traffic readings."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class TrafficReadingCreate(BaseModel):
    stop_id: int = Field(..., ge=1)
    recorded_at: str = ...
    traffic_level: Literal['low', 'medium', 'high', 'severe'] = ...
    vehicle_density: Optional[float] = Field(None, ge=0, le=500)
    avg_speed: Optional[float] = Field(None, ge=0, le=120)
    road_occupancy: Optional[float] = Field(None, ge=0, le=1)
    traffic_flow: Optional[float] = Field(None, ge=0, le=5000)
    source: Literal['sensor', 'manual', 'simulated'] = 'sensor'


class TrafficReadingUpdate(BaseModel):
    """Send only the fields you want to change."""
    stop_id: Optional[int] = Field(None, ge=1)
    recorded_at: Optional[str] = None
    traffic_level: Optional[Literal['low', 'medium', 'high', 'severe']] = None
    vehicle_density: Optional[float] = Field(None, ge=0, le=500)
    avg_speed: Optional[float] = Field(None, ge=0, le=120)
    road_occupancy: Optional[float] = Field(None, ge=0, le=1)
    traffic_flow: Optional[float] = Field(None, ge=0, le=5000)
    source: Optional[Literal['sensor', 'manual', 'simulated']] = None


class TrafficReadingOut(BaseModel):
    id: int
    stop_id: Optional[int] = None
    recorded_at: Optional[str] = None
    traffic_level: Optional[str] = None
    vehicle_density: Optional[float] = None
    avg_speed: Optional[float] = None
    road_occupancy: Optional[float] = None
    traffic_flow: Optional[float] = None
    source: Optional[str] = None
    created_at: str
    updated_at: str


class TrafficReadingPage(BaseModel):
    items: list[TrafficReadingOut]
    total: int
    limit: int
    offset: int
