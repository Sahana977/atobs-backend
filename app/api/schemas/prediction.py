"""Request/response shapes for the API."""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

TrafficLevel = Literal["low", "medium", "high", "severe"]


class OccupancyRequest(BaseModel):
    trip_id: str = Field(..., examples=["T012"])
    stop_id: str = Field(..., examples=["S05"])
    travel_time: datetime = Field(default_factory=datetime.now)
    traffic_level: TrafficLevel = "medium"
    delay_min: float = Field(0.0, ge=0, le=120)
    # Optional live sensor values; defaults per traffic_level are used if omitted
    vehicle_density: Optional[float] = None
    avg_speed: Optional[float] = None
    road_occupancy: Optional[float] = Field(None, ge=0, le=1)
    traffic_flow: Optional[float] = None


class OccupancyResponse(BaseModel):
    trip_id: str
    stop_id: str
    predicted_occupancy_pct: float
    comfort: str
    is_peak_hour: bool
    model: str


class BatchOccupancyRequest(BaseModel):
    items: list[OccupancyRequest] = Field(..., min_length=1, max_length=500)


class RouteRequest(BaseModel):
    origin: str = Field(..., examples=["Marathahalli Bridge"])
    destination: str = Field(..., examples=["Whitefield"])
    travel_time: datetime = Field(default_factory=datetime.now)
    traffic_level: TrafficLevel = "medium"
    comfort_weight: float = Field(0.15, ge=0, le=2,
                                  description="0 = fastest only; higher = avoid crowding more")


class TripPredictionRequest(BaseModel):
    traffic_level: TrafficLevel = "medium"
    delay_min: float = Field(0.0, ge=0, le=120)
