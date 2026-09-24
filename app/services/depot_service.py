"""Business rules for depots: validation, reference checks, uniqueness."""
import csv
import io
import sqlite3
from datetime import datetime
from typing import Optional

from app import database
from app.errors import ConflictError, NotFoundError, ValidationError
from app.models.depot import Depot, FIELDS
from app.repositories import depot_repo as repo

REQUIRED_FIELDS = ("depot_code", "name",)
MAX_PAGE_SIZE = 500


def _is_blank(value) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _validate(data: dict, partial: bool = False) -> dict:
    """Check every field. With partial=True only the fields present are checked."""
    errors: dict[str, str] = {}
    for name in REQUIRED_FIELDS:
        if (not partial or name in data) and _is_blank(data.get(name)):
            errors[name] = "is required"

    # depot_code
    value = data.get("depot_code")
    if value is not None and "depot_code" not in errors:
        if not isinstance(value, str):
            errors["depot_code"] = "must be text"
        elif len(value) > 20:
            errors["depot_code"] = "must be at most 20 characters"
        else:
            data["depot_code"] = value.strip()

    # name
    value = data.get("name")
    if value is not None and "name" not in errors:
        if not isinstance(value, str):
            errors["name"] = "must be text"
        elif len(value) > 200:
            errors["name"] = "must be at most 200 characters"
        else:
            data["name"] = value.strip()

    # area
    value = data.get("area")
    if value is not None and "area" not in errors:
        if not isinstance(value, str):
            errors["area"] = "must be text"
        elif len(value) > 200:
            errors["area"] = "must be at most 200 characters"
        else:
            data["area"] = value.strip()

    # capacity
    value = data.get("capacity")
    if value is not None and "capacity" not in errors:
        if isinstance(value, bool) or not isinstance(value, int):
            errors["capacity"] = "must be a whole number"
        elif value < 1:
            errors["capacity"] = "must be at least 1"
        elif value > 1000:
            errors["capacity"] = "must be at most 1000"

    # latitude
    value = data.get("latitude")
    if value is not None and "latitude" not in errors:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors["latitude"] = "must be a number"
        elif value < -90:
            errors["latitude"] = "must be at least -90"
        elif value > 90:
            errors["latitude"] = "must be at most 90"
        else:
            data["latitude"] = float(value)

    # longitude
    value = data.get("longitude")
    if value is not None and "longitude" not in errors:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors["longitude"] = "must be a number"
        elif value < -180:
            errors["longitude"] = "must be at least -180"
        elif value > 180:
            errors["longitude"] = "must be at most 180"
        else:
            data["longitude"] = float(value)

    # is_active
    value = data.get("is_active")
    if value is not None and "is_active" not in errors:
        if not isinstance(value, bool):
            errors["is_active"] = "must be true or false"

    if errors:
        raise ValidationError(errors)
    return data


def _check_references(conn: sqlite3.Connection, data: dict) -> None:
    return None


def _check_unique(conn: sqlite3.Connection, data: dict, current_id: Optional[int] = None) -> None:
    value = data.get("depot_code")
    if value is not None:
        existing = repo.get_by_depot_code(conn, value)
        if existing is not None and existing.id != current_id:
            raise ConflictError(f"depot with depot_code '{value}' already exists")


def create(data: dict) -> Depot:
    data = _validate(dict(data))
    with database.session() as conn:
        _check_references(conn, data)
        _check_unique(conn, data)
        try:
            return repo.create(conn, data)
        except sqlite3.IntegrityError as exc:
            raise ConflictError(str(exc)) from exc


def get(item_id: int) -> Depot:
    with database.session() as conn:
        item = repo.get(conn, item_id)
    if item is None:
        raise NotFoundError(f"depot {item_id} not found")
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


def update(item_id: int, changes: dict) -> Depot:
    changes = _validate(dict(changes), partial=True)
    with database.session() as conn:
        current = repo.get(conn, item_id)
        if current is None:
            raise NotFoundError(f"depot {item_id} not found")
        _check_references(conn, changes)
        _check_unique(conn, changes, current_id=item_id)
        try:
            return repo.update(conn, item_id, changes)
        except sqlite3.IntegrityError as exc:
            raise ConflictError(str(exc)) from exc


def delete(item_id: int) -> None:
    with database.session() as conn:
        if not repo.exists(conn, item_id):
            raise NotFoundError(f"depot {item_id} not found")
        try:
            repo.delete(conn, item_id)
        except sqlite3.IntegrityError as exc:
            raise ConflictError("depot is still referenced by other records") from exc


def bulk_create(items: list[dict]) -> list[Depot]:
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
