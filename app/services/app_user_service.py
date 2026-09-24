"""Business rules for users: validation, reference checks, uniqueness."""
import csv
import io
import sqlite3
from datetime import datetime
from typing import Optional

from app import database
from app.errors import ConflictError, NotFoundError, ValidationError
from app.models.app_user import AppUser, FIELDS, ROLE_CHOICES
from app.repositories import app_user_repo as repo
from app.repositories import stop_repo

REQUIRED_FIELDS = ("email", "full_name",)
MAX_PAGE_SIZE = 500


def _is_blank(value) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _validate(data: dict, partial: bool = False) -> dict:
    """Check every field. With partial=True only the fields present are checked."""
    errors: dict[str, str] = {}
    for name in REQUIRED_FIELDS:
        if (not partial or name in data) and _is_blank(data.get(name)):
            errors[name] = "is required"

    # email
    value = data.get("email")
    if value is not None and "email" not in errors:
        if not isinstance(value, str):
            errors["email"] = "must be text"
        elif len(value) > 120:
            errors["email"] = "must be at most 120 characters"
        else:
            data["email"] = value.strip()

    # full_name
    value = data.get("full_name")
    if value is not None and "full_name" not in errors:
        if not isinstance(value, str):
            errors["full_name"] = "must be text"
        elif len(value) > 200:
            errors["full_name"] = "must be at most 200 characters"
        else:
            data["full_name"] = value.strip()

    # role
    value = data.get("role")
    if value is not None and "role" not in errors:
        if not isinstance(value, str):
            errors["role"] = "must be text"
        elif len(value) > 200:
            errors["role"] = "must be at most 200 characters"
        elif value not in ROLE_CHOICES:
            errors["role"] = "must be one of: " + ", ".join(ROLE_CHOICES)
        else:
            data["role"] = value.strip()

    # home_stop_id
    value = data.get("home_stop_id")
    if value is not None and "home_stop_id" not in errors:
        if isinstance(value, bool) or not isinstance(value, int):
            errors["home_stop_id"] = "must be a whole number"
        elif value < 1:
            errors["home_stop_id"] = "must be a valid id"

    # is_active
    value = data.get("is_active")
    if value is not None and "is_active" not in errors:
        if not isinstance(value, bool):
            errors["is_active"] = "must be true or false"

    # cross-field rules
    email = data.get("email")
    if "email" not in errors and isinstance(email, str) and ("@" not in email or "." not in email.split("@")[-1]):
        errors["email"] = "must be a valid email address"
    elif "email" not in errors and isinstance(email, str):
        data["email"] = email.lower()

    if errors:
        raise ValidationError(errors)
    return data


def _check_references(conn: sqlite3.Connection, data: dict) -> None:
    errors: dict[str, str] = {}
    if data.get("home_stop_id") is not None and not stop_repo.exists(conn, data["home_stop_id"]):
        errors["home_stop_id"] = "stop not found"
    if errors:
        raise ValidationError(errors)


def _check_unique(conn: sqlite3.Connection, data: dict, current_id: Optional[int] = None) -> None:
    value = data.get("email")
    if value is not None:
        existing = repo.get_by_email(conn, value)
        if existing is not None and existing.id != current_id:
            raise ConflictError(f"app user with email '{value}' already exists")


def create(data: dict) -> AppUser:
    data = _validate(dict(data))
    with database.session() as conn:
        _check_references(conn, data)
        _check_unique(conn, data)
        try:
            return repo.create(conn, data)
        except sqlite3.IntegrityError as exc:
            raise ConflictError(str(exc)) from exc


def get(item_id: int) -> AppUser:
    with database.session() as conn:
        item = repo.get(conn, item_id)
    if item is None:
        raise NotFoundError(f"app user {item_id} not found")
    return item


def list_(filters: Optional[dict] = None, limit: int = 50, offset: int = 0,
          order_by: str = "id", descending: bool = False) -> dict:
    limit = max(1, min(limit, MAX_PAGE_SIZE))
    offset = max(0, offset)
    with database.session() as conn:
        items = repo.list_(conn, filters, limit, offset, order_by, descending)
        total = repo.count(conn, filters)
    return {"items": [i.to_dict() for i in items], "total": total, "limit": limit, "offset": offset}


def count(filters: Optional[dict] = None) -> int:
    with database.session() as conn:
        return repo.count(conn, filters)


def update(item_id: int, changes: dict) -> AppUser:
    changes = _validate(dict(changes), partial=True)
    with database.session() as conn:
        current = repo.get(conn, item_id)
        if current is None:
            raise NotFoundError(f"app user {item_id} not found")
        # re-run cross-field rules against the merged record
        merged = {**current.to_dict(), **{k: v for k, v in changes.items() if v is not None}}
        _validate({k: merged[k] for k in FIELDS}, partial=True)
        _check_references(conn, changes)
        _check_unique(conn, changes, current_id=item_id)
        try:
            return repo.update(conn, item_id, changes)
        except sqlite3.IntegrityError as exc:
            raise ConflictError(str(exc)) from exc


def delete(item_id: int) -> None:
    with database.session() as conn:
        if not repo.exists(conn, item_id):
            raise NotFoundError(f"app user {item_id} not found")
        try:
            repo.delete(conn, item_id)
        except sqlite3.IntegrityError as exc:
            raise ConflictError("app user is still referenced by other records") from exc


def bulk_create(items: list[dict]) -> list[AppUser]:
    """All-or-nothing: if any item is invalid, nothing is saved."""
    cleaned = []
    for index, item in enumerate(items):
        try:
            cleaned.append(_validate(dict(item)))
        except ValidationError as exc:
            raise ValidationError({f"items[{index}].{k}": v for k, v in exc.errors.items()}) from exc
    with database.session() as conn:
        for item in cleaned:
            _check_references(conn, item)
            _check_unique(conn, item)
        try:
            return repo.bulk_create(conn, cleaned)
        except sqlite3.IntegrityError as exc:
            raise ConflictError(str(exc)) from exc


def export_csv(filters: Optional[dict] = None) -> str:
    with database.session() as conn:
        items = repo.list_(conn, filters, limit=1_000_000)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["id", *FIELDS, "created_at", "updated_at"])
    writer.writeheader()
    for item in items:
        writer.writerow(item.to_dict())
    return buffer.getvalue()
