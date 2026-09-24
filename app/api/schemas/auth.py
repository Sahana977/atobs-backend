"""Request shapes for /auth."""
from typing import Literal

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str = Field(..., max_length=120, examples=["commuter@example.com"])
    full_name: str = Field(..., max_length=200)
    password: str = Field(..., min_length=8, max_length=128)
    role: Literal["commuter", "operator", "admin"] = "commuter"


class LoginRequest(BaseModel):
    email: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
