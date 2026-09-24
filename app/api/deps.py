"""Shared FastAPI dependencies."""
from fastapi import Header

from app.errors import AuthError
from app.models.app_user import AppUser
from app.services import auth_service


def bearer_token(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthError("send header: Authorization: Bearer <token>")
    return authorization.split(" ", 1)[1].strip()


def current_user(authorization: str = Header(None)) -> AppUser:
    return auth_service.current_user(bearer_token(authorization))
