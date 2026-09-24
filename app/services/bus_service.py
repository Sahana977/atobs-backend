"""Business rules for buses: validation, reference checks, uniqueness."""
import csv
import io
import sqlite3
from datetime import datetime
from typing import Optional

from app import database
from app.errors import ConflictError, NotFoundError, ValidationError
from app.models.bus import Bus, FIELDS, BUS_TYPE_CHOICES
from app.repositories import bus_repo as repo
from app.repositories import depot_repo

REQUIRED_FIELDS = ("registration_no", "depot_id",)
MAX_PAGE_SIZE = 500


def _is_blank(value) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _validate(data: dict, partial: bool = False) -> dict:
    """Check every field. With partial=True only the fields present are checked."""
    errors: dict[str, str] = {}
    for name in REQUIRED_FIELDS:
        if (not partial or name in data) and _is_blank(data.get(name)):
            errors[name] = "is required"

    # registration_no
    value = data.get("registration_no")
    if value is not None and "registration_no" not in errors:
        if not isinstance(value, str):
            errors["registration_no"] = "must be text"
        elif len(value) > 20:
            errors["registration_no"] = "must be at most 20 characters"
        else:
            data["registration_no"] = value.strip()

    # depot_id
    value = data.get("depot_id")
    if value is not None and "depot_id" not in errors:
        if isinstance(value, bool) or not isinstance(value, int):
            errors["depot_id"] = "must be a whole number"
        elif value < 1:
            errors["depot_id"] = "must be a valid id"

    # capacity
    value = data.get("capacity")
    if value is not None and "capacity" not in errors:
        if isinstance(value, bool) or not isinstance(value, int):
            errors["capacity"] = "must be a whole number"
        elif value < 10:
            errors["capacity"] = "must be at least 10"
        elif value > 150:
            errors["capacity"] = "must be at most 150"

    # bus_type
    value = data.get("bus_type")
    if value is not None and "bus_type" not in errors:
        if not isinstance(value, str):
            errors["bus_type"] = "must be text"
        elif len(value) > 200:
            errors["bus_type"] = "must be at most 200 characters"
        elif value not in BUS_TYPE_CHOICES:
            errors["bus_type"] = "must be one of: " + ", ".join(BUS_TYPE_CHOICES)
        else:
            data["bus_type"] = value.strip()

    # manufacture_year
    value = data.get("manufacture_year")
    if value is not None and "manufacture_year" not in errors:
        if isinstance(value, bool) or not isinstance(value, int):
            errors["manufacture_year"] = "must be a whole number"
        elif value < 1990:
            errors["manufacture_year"] = "must be at least 1990"
        elif value > 2030:
            errors["manufacture_year"] = "must be at most 2030"

    # is_operational
    value = data.get("is_operational")
    if value is not None and "is_operational" not in errors:
        if not isinstance(value, bool):
            errors["is_operational"] = "must be true or false"

    if errors:
        raise ValidationError(errors)
    return data


def _check_references(conn: sqlite3.Connection, data: dict) -> None:
    errors: dict[str, str] = {}
    if data.get("depot_id") is not None and not depot_repo.exists(conn, data["depot_id"]):
        errors["depot_id"] = "depot not found"
    if errors:
        raise ValidationError(errors)


def _check_unique(conn: sqlite3.Connection, data: dict, current_id: Optional[int] = None) -> None:
    value = data.get("registration_no")
    if value is not None:
        existing = repo.get_by_registration_no(conn, value)
        if existing is not None and existing.id != current_id:
            raise ConflictError(f"bus with registration_no '{value}' already exists")


def create(data: dict) -> Bus:
    data = _validate(dict(data))
    with database.session() as conn:
        _check_references(conn, data)
        _check_unique(conn, data)
        try:
            return repo.create(conn, data)
        except sqlite3.IntegrityError as exc:
            raise ConflictError(str(exc)) from exc


def get(item_id: int) -> Bus:
    with database.session() as conn:
        item = repo.get(conn, item_id)
    if item is None:
        raise NotFoundError(f"bus {item_id} not found")
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


def update(item_id: int, changes: dict) -> Bus:
    changes = _validate(dict(changes), partial=True)
    with database.session() as conn:
        current = repo.get(conn, item_id)
        if current is None:
            raise NotFoundError(f"bus {item_id} not found")
        _check_references(conn, changes)
        _check_unique(conn, changes, current_id=item_id)
        try:
            return repo.update(conn, item_id, changes)
        except sqlite3.IntegrityError as exc:
            raise ConflictError(str(exc)) from exc


def delete(item_id: int) -> None:
    with database.session() as conn:
        if not repo.exists(conn, item_id):
            raise NotFoundError(f"bus {item_id} not found")
        try:
            repo.delete(conn, item_id)
        except sqlite3.IntegrityError as exc:
            raise ConflictError("bus is still referenced by other records") from exc


def bulk_create(items: list[dict]) -> list[Bus]:
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
