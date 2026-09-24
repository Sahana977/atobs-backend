"""Request/response schemas for stops."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class StopCreate(BaseModel):
    stop_code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=200)
    area: Optional[str] = Field(None, max_length=200)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    zone: Literal['core', 'suburban', 'outer'] = 'core'
    has_shelter: bool = False
    is_accessible: bool = True


class StopUpdate(BaseModel):
    """Send only the fields you want to change."""
    stop_code: Optional[str] = Field(None, max_length=20)
    name: Optional[str] = Field(None, max_length=200)
    area: Optional[str] = Field(None, max_length=200)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    zone: Optional[Literal['core', 'suburban', 'outer']] = None
    has_shelter: Optional[bool] = None
    is_accessible: Optional[bool] = None


class StopOut(BaseModel):
    id: int
    stop_code: Optional[str] = None
    name: Optional[str] = None
    area: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    zone: Optional[str] = None
    has_shelter: Optional[bool] = None
    is_accessible: Optional[bool] = None
    created_at: str
    updated_at: str


class StopPage(BaseModel):
    items: list[StopOut]
    total: int
    limit: int
    offset: int
