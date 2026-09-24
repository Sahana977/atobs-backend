"""Request/response schemas for alerts."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class AlertCreate(BaseModel):
    title: str = Field(..., max_length=200)
    message: str = Field(..., max_length=2000)
    severity: Literal['info', 'warning', 'critical'] = 'info'
    stop_id: Optional[int] = Field(None, ge=1)
    route_id: Optional[int] = Field(None, ge=1)
    starts_at: str = ...
    ends_at: Optional[str] = None
    is_active: bool = True


class AlertUpdate(BaseModel):
    """Send only the fields you want to change."""
    title: Optional[str] = Field(None, max_length=200)
    message: Optional[str] = Field(None, max_length=2000)
    severity: Optional[Literal['info', 'warning', 'critical']] = None
    stop_id: Optional[int] = Field(None, ge=1)
    route_id: Optional[int] = Field(None, ge=1)
    starts_at: Optional[str] = None
    ends_at: Optional[str] = None
    is_active: Optional[bool] = None


class AlertOut(BaseModel):
    id: int
    title: Optional[str] = None
    message: Optional[str] = None
    severity: Optional[str] = None
    stop_id: Optional[int] = None
    route_id: Optional[int] = None
    starts_at: Optional[str] = None
    ends_at: Optional[str] = None
    is_active: Optional[bool] = None
    created_at: str
    updated_at: str


class AlertPage(BaseModel):
    items: list[AlertOut]
    total: int
    limit: int
    offset: int
