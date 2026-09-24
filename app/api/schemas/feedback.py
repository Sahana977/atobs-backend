"""Request/response schemas for feedback."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    user_id: Optional[int] = Field(None, ge=1)
    trip_id: Optional[int] = Field(None, ge=1)
    rating: int = Field(..., ge=1, le=5)
    comfort_rating: Optional[int] = Field(None, ge=1, le=5)
    category: Literal['crowding', 'delay', 'cleanliness', 'staff', 'other'] = 'other'
    comment: Optional[str] = Field(None, max_length=2000)


class FeedbackUpdate(BaseModel):
    """Send only the fields you want to change."""
    user_id: Optional[int] = Field(None, ge=1)
    trip_id: Optional[int] = Field(None, ge=1)
    rating: Optional[int] = Field(None, ge=1, le=5)
    comfort_rating: Optional[int] = Field(None, ge=1, le=5)
    category: Optional[Literal['crowding', 'delay', 'cleanliness', 'staff', 'other']] = None
    comment: Optional[str] = Field(None, max_length=2000)


class FeedbackOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    trip_id: Optional[int] = None
    rating: Optional[int] = None
    comfort_rating: Optional[int] = None
    category: Optional[str] = None
    comment: Optional[str] = None
    created_at: str
    updated_at: str


class FeedbackPage(BaseModel):
    items: list[FeedbackOut]
    total: int
    limit: int
    offset: int
