"""Request/response schemas for depots."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class DepotCreate(BaseModel):
    depot_code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=200)
    area: Optional[str] = Field(None, max_length=200)
    capacity: int = Field(100, ge=1, le=1000)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    is_active: bool = True


class DepotUpdate(BaseModel):
    """Send only the fields you want to change."""
    depot_code: Optional[str] = Field(None, max_length=20)
    name: Optional[str] = Field(None, max_length=200)
    area: Optional[str] = Field(None, max_length=200)
    capacity: Optional[int] = Field(None, ge=1, le=1000)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    is_active: Optional[bool] = None


class DepotOut(BaseModel):
    id: int
    depot_code: Optional[str] = None
    name: Optional[str] = None
    area: Optional[str] = None
    capacity: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: Optional[bool] = None
    created_at: str
    updated_at: str


class DepotPage(BaseModel):
    items: list[DepotOut]
    total: int
    limit: int
    offset: int
