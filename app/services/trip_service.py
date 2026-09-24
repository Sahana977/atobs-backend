"""Business rules for trips: validation, reference checks, uniqueness."""
import csv
import io
import sqlite3
from datetime import datetime
from typing import Optional

from app import database
from app.errors import ConflictError, NotFoundError, ValidationError
from app.models.trip import Trip, FIELDS, STATUS_CHOICES
from app.repositories import trip_repo as repo
from app.repositories import bus_repo
from app.repositories import route_repo

REQUIRED_FIELDS = ("trip_code", "route_id", "bus_id", "scheduled_start",)
MAX_PAGE_SIZE = 500


def _is_blank(value) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _validate(data: dict, partial: bool = False) -> dict:
    """Check every field. With partial=True only the fields present are checked."""
    errors: dict[str, str] = {}
    for name in REQUIRED_FIELDS:
        if (not partial or name in data) and _is_blank(data.get(name)):
            errors[name] = "is required"

    # trip_code
    value = data.get("trip_code")
    if value is not None and "trip_code" not in errors:
        if not isinstance(value, str):
            errors["trip_code"] = "must be text"
        elif len(value) > 30:
            errors["trip_code"] = "must be at most 30 characters"
        else:
            data["trip_code"] = value.strip()

    # route_id
    value = data.get("route_id")
    if value is not None and "route_id" not in errors:
        if isinstance(value, bool) or not isinstance(value, int):
            errors["route_id"] = "must be a whole number"
        elif value < 1:
            errors["route_id"] = "must be a valid id"

    # bus_id
    value = data.get("bus_id")
    if value is not None and "bus_id" not in errors:
        if isinstance(value, bool) or not isinstance(value, int):
            errors["bus_id"] = "must be a whole number"
        elif value < 1:
            errors["bus_id"] = "must be a valid id"

    # scheduled_start
    value = data.get("scheduled_start")
    if value is not None and "scheduled_start" not in errors:
        if not isinstance(value, str):
            errors["scheduled_start"] = "must be an ISO date-time string"
        else:
            try:
                data["scheduled_start"] = datetime.fromisoformat(value).isoformat(timespec="seconds")
            except ValueError:
                errors["scheduled_start"] = "must be an ISO date-time like 2026-10-01T08:30:00"

    # scheduled_end
    value = data.get("scheduled_end")
    if value is not None and "scheduled_end" not in errors:
        if not isinstance(value, str):
            errors["scheduled_end"] = "must be an ISO date-time string"
        else:
            try:
                data["scheduled_end"] = datetime.fromisoformat(value).isoformat(timespec="seconds")
            except ValueError:
                errors["scheduled_end"] = "must be an ISO date-time like 2026-10-01T08:30:00"

    # status
    value = data.get("status")
    if value is not None and "status" not in errors:
        if not isinstance(value, str):
            errors["status"] = "must be text"
        elif len(value) > 200:
            errors["status"] = "must be at most 200 characters"
        elif value not in STATUS_CHOICES:
            errors["status"] = "must be one of: " + ", ".join(STATUS_CHOICES)
        else:
            data["status"] = value.strip()

    # cross-field rules
    start, end = data.get("scheduled_start"), data.get("scheduled_end")
    if "scheduled_start" not in errors and "scheduled_end" not in errors and start and end and end <= start:
        errors["scheduled_end"] = "must be after scheduled_start"

    if errors:
        raise ValidationError(errors)
    return data


def _check_references(conn: sqlite3.Connection, data: dict) -> None:
    errors: dict[str, str] = {}
    if data.get("route_id") is not None and not route_repo.exists(conn, data["route_id"]):
        errors["route_id"] = "route not found"
    if data.get("bus_id") is not None and not bus_repo.exists(conn, data["bus_id"]):
        errors["bus_id"] = "bus not found"
    if errors:
        raise ValidationError(errors)


def _check_unique(conn: sqlite3.Connection, data: dict, current_id: Optional[int] = None) -> None:
    value = data.get("trip_code")
    if value is not None:
        existing = repo.get_by_trip_code(conn, value)
        if existing is not None and existing.id != current_id:
            raise ConflictError(f"trip with trip_code '{value}' already exists")


def create(data: dict) -> Trip:
    data = _validate(dict(data))
    with database.session() as conn:
        _check_references(conn, data)
        _check_unique(conn, data)
        try:
            return repo.create(conn, data)
        except sqlite3.IntegrityError as exc:
            raise ConflictError(str(exc)) from exc


def get(item_id: int) -> Trip:
    with database.session() as conn:
        item = repo.get(conn, item_id)
    if item is None:
        raise NotFoundError(f"trip {item_id} not found")
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


def update(item_id: int, changes: dict) -> Trip:
    changes = _validate(dict(changes), partial=True)
    with database.session() as conn:
        current = repo.get(conn, item_id)
        if current is None:
            raise NotFoundError(f"trip {item_id} not found")
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
            raise NotFoundError(f"trip {item_id} not found")
        try:
            repo.delete(conn, item_id)
        except sqlite3.IntegrityError as exc:
            raise ConflictError("trip is still referenced by other records") from exc


def bulk_create(items: list[dict]) -> list[Trip]:
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
