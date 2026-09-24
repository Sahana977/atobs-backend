"""Business rules for routes: validation, reference checks, uniqueness."""
import csv
import io
import sqlite3
from datetime import datetime
from typing import Optional

from app import database
from app.errors import ConflictError, NotFoundError, ValidationError
from app.models.route import Route, FIELDS, SERVICE_TYPE_CHOICES
from app.repositories import route_repo as repo
from app.repositories import stop_repo

REQUIRED_FIELDS = ("route_number", "name", "origin_stop_id", "destination_stop_id", "distance_km",)
MAX_PAGE_SIZE = 500


def _is_blank(value) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _validate(data: dict, partial: bool = False) -> dict:
    """Check every field. With partial=True only the fields present are checked."""
    errors: dict[str, str] = {}
    for name in REQUIRED_FIELDS:
        if (not partial or name in data) and _is_blank(data.get(name)):
            errors[name] = "is required"

    # route_number
    value = data.get("route_number")
    if value is not None and "route_number" not in errors:
        if not isinstance(value, str):
            errors["route_number"] = "must be text"
        elif len(value) > 20:
            errors["route_number"] = "must be at most 20 characters"
        else:
            data["route_number"] = value.strip()

    # name
    value = data.get("name")
    if value is not None and "name" not in errors:
        if not isinstance(value, str):
            errors["name"] = "must be text"
        elif len(value) > 200:
            errors["name"] = "must be at most 200 characters"
        else:
            data["name"] = value.strip()

    # origin_stop_id
    value = data.get("origin_stop_id")
    if value is not None and "origin_stop_id" not in errors:
        if isinstance(value, bool) or not isinstance(value, int):
            errors["origin_stop_id"] = "must be a whole number"
        elif value < 1:
            errors["origin_stop_id"] = "must be a valid id"

    # destination_stop_id
    value = data.get("destination_stop_id")
    if value is not None and "destination_stop_id" not in errors:
        if isinstance(value, bool) or not isinstance(value, int):
            errors["destination_stop_id"] = "must be a whole number"
        elif value < 1:
            errors["destination_stop_id"] = "must be a valid id"

    # distance_km
    value = data.get("distance_km")
    if value is not None and "distance_km" not in errors:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors["distance_km"] = "must be a number"
        elif value < 0.1:
            errors["distance_km"] = "must be at least 0.1"
        elif value > 200:
            errors["distance_km"] = "must be at most 200"
        else:
            data["distance_km"] = float(value)

    # service_type
    value = data.get("service_type")
    if value is not None and "service_type" not in errors:
        if not isinstance(value, str):
            errors["service_type"] = "must be text"
        elif len(value) > 200:
            errors["service_type"] = "must be at most 200 characters"
        elif value not in SERVICE_TYPE_CHOICES:
            errors["service_type"] = "must be one of: " + ", ".join(SERVICE_TYPE_CHOICES)
        else:
            data["service_type"] = value.strip()

    # avg_headway_min
    value = data.get("avg_headway_min")
    if value is not None and "avg_headway_min" not in errors:
        if isinstance(value, bool) or not isinstance(value, int):
            errors["avg_headway_min"] = "must be a whole number"
        elif value < 1:
            errors["avg_headway_min"] = "must be at least 1"
        elif value > 180:
            errors["avg_headway_min"] = "must be at most 180"

    # is_active
    value = data.get("is_active")
    if value is not None and "is_active" not in errors:
        if not isinstance(value, bool):
            errors["is_active"] = "must be true or false"

    # cross-field rules
    if data.get("origin_stop_id") is not None and data.get("origin_stop_id") == data.get("destination_stop_id"):
        errors["destination_stop_id"] = "must be different from origin_stop_id"

    if errors:
        raise ValidationError(errors)
    return data


def _check_references(conn: sqlite3.Connection, data: dict) -> None:
    errors: dict[str, str] = {}
    if data.get("origin_stop_id") is not None and not stop_repo.exists(conn, data["origin_stop_id"]):
        errors["origin_stop_id"] = "stop not found"
    if data.get("destination_stop_id") is not None and not stop_repo.exists(conn, data["destination_stop_id"]):
        errors["destination_stop_id"] = "stop not found"
    if errors:
        raise ValidationError(errors)


def _check_unique(conn: sqlite3.Connection, data: dict, current_id: Optional[int] = None) -> None:
    value = data.get("route_number")
    if value is not None:
        existing = repo.get_by_route_number(conn, value)
        if existing is not None and existing.id != current_id:
            raise ConflictError(f"route with route_number '{value}' already exists")


def create(data: dict) -> Route:
    data = _validate(dict(data))
    with database.session() as conn:
        _check_references(conn, data)
        _check_unique(conn, data)
        try:
            return repo.create(conn, data)
        except sqlite3.IntegrityError as exc:
            raise ConflictError(str(exc)) from exc


def get(item_id: int) -> Route:
    with database.session() as conn:
        item = repo.get(conn, item_id)
    if item is None:
        raise NotFoundError(f"route {item_id} not found")
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


def update(item_id: int, changes: dict) -> Route:
    changes = _validate(dict(changes), partial=True)
    with database.session() as conn:
        current = repo.get(conn, item_id)
        if current is None:
            raise NotFoundError(f"route {item_id} not found")
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
            raise NotFoundError(f"route {item_id} not found")
        try:
            repo.delete(conn, item_id)
        except sqlite3.IntegrityError as exc:
            raise ConflictError("route is still referenced by other records") from exc


def bulk_create(items: list[dict]) -> list[Route]:
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
