"""Request/response schemas for route stops."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class RouteStopCreate(BaseModel):
    route_id: int = Field(..., ge=1)
    stop_id: int = Field(..., ge=1)
    sequence: int = Field(..., ge=1, le=200)
    minutes_from_start: float = Field(0.0, ge=0, le=600)


class RouteStopUpdate(BaseModel):
    """Send only the fields you want to change."""
    route_id: Optional[int] = Field(None, ge=1)
    stop_id: Optional[int] = Field(None, ge=1)
    sequence: Optional[int] = Field(None, ge=1, le=200)
    minutes_from_start: Optional[float] = Field(None, ge=0, le=600)


class RouteStopOut(BaseModel):
    id: int
    route_id: Optional[int] = None
    stop_id: Optional[int] = None
    sequence: Optional[int] = None
    minutes_from_start: Optional[float] = None
    created_at: str
    updated_at: str


class RouteStopPage(BaseModel):
    items: list[RouteStopOut]
    total: int
    limit: int
    offset: int
