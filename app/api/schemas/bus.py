"""Request/response schemas for buses."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class BusCreate(BaseModel):
    registration_no: str = Field(..., max_length=20)
    depot_id: int = Field(..., ge=1)
    capacity: int = Field(60, ge=10, le=150)
    bus_type: Literal['ordinary', 'ac', 'electric', 'midi'] = 'ordinary'
    manufacture_year: Optional[int] = Field(None, ge=1990, le=2030)
    is_operational: bool = True


class BusUpdate(BaseModel):
    """Send only the fields you want to change."""
    registration_no: Optional[str] = Field(None, max_length=20)
    depot_id: Optional[int] = Field(None, ge=1)
    capacity: Optional[int] = Field(None, ge=10, le=150)
    bus_type: Optional[Literal['ordinary', 'ac', 'electric', 'midi']] = None
    manufacture_year: Optional[int] = Field(None, ge=1990, le=2030)
    is_operational: Optional[bool] = None


class BusOut(BaseModel):
    id: int
    registration_no: Optional[str] = None
    depot_id: Optional[int] = None
    capacity: Optional[int] = None
    bus_type: Optional[str] = None
    manufacture_year: Optional[int] = None
    is_operational: Optional[bool] = None
    created_at: str
    updated_at: str


class BusPage(BaseModel):
    items: list[BusOut]
    total: int
    limit: int
    offset: int
