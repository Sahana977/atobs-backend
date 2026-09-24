"""Request/response schemas for users."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class AppUserCreate(BaseModel):
    email: str = Field(..., max_length=120)
    full_name: str = Field(..., max_length=200)
    role: Literal['commuter', 'operator', 'admin'] = 'commuter'
    home_stop_id: Optional[int] = Field(None, ge=1)
    is_active: bool = True


class AppUserUpdate(BaseModel):
    """Send only the fields you want to change."""
    email: Optional[str] = Field(None, max_length=120)
    full_name: Optional[str] = Field(None, max_length=200)
    role: Optional[Literal['commuter', 'operator', 'admin']] = None
    home_stop_id: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None


class AppUserOut(BaseModel):
    id: int
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    home_stop_id: Optional[int] = None
    is_active: Optional[bool] = None
    created_at: str
    updated_at: str


class AppUserPage(BaseModel):
    items: list[AppUserOut]
    total: int
    limit: int
    offset: int
