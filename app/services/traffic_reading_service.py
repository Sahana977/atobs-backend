"""Business rules for traffic readings: validation, reference checks, uniqueness."""
import csv
import io
import sqlite3
from datetime import datetime
from typing import Optional

from app import database
from app.errors import ConflictError, NotFoundError, ValidationError
from app.models.traffic_reading import TrafficReading, FIELDS, TRAFFIC_LEVEL_CHOICES, SOURCE_CHOICES
from app.repositories import traffic_reading_repo as repo
from app.repositories import stop_repo

REQUIRED_FIELDS = ("stop_id", "recorded_at", "traffic_level",)
MAX_PAGE_SIZE = 500


def _is_blank(value) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _validate(data: dict, partial: bool = False) -> dict:
    """Check every field. With partial=True only the fields present are checked."""
    errors: dict[str, str] = {}
    for name in REQUIRED_FIELDS:
        if (not partial or name in data) and _is_blank(data.get(name)):
            errors[name] = "is required"

    # stop_id
    value = data.get("stop_id")
    if value is not None and "stop_id" not in errors:
        if isinstance(value, bool) or not isinstance(value, int):
            errors["stop_id"] = "must be a whole number"
        elif value < 1:
            errors["stop_id"] = "must be a valid id"

    # recorded_at
    value = data.get("recorded_at")
    if value is not None and "recorded_at" not in errors:
        if not isinstance(value, str):
            errors["recorded_at"] = "must be an ISO date-time string"
        else:
            try:
                data["recorded_at"] = datetime.fromisoformat(value).isoformat(timespec="seconds")
            except ValueError:
                errors["recorded_at"] = "must be an ISO date-time like 2026-10-01T08:30:00"

    # traffic_level
    value = data.get("traffic_level")
    if value is not None and "traffic_level" not in errors:
        if not isinstance(value, str):
            errors["traffic_level"] = "must be text"
        elif len(value) > 200:
            errors["traffic_level"] = "must be at most 200 characters"
        elif value not in TRAFFIC_LEVEL_CHOICES:
            errors["traffic_level"] = "must be one of: " + ", ".join(TRAFFIC_LEVEL_CHOICES)
        else:
            data["traffic_level"] = value.strip()

    # vehicle_density
    value = data.get("vehicle_density")
    if value is not None and "vehicle_density" not in errors:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors["vehicle_density"] = "must be a number"
        elif value < 0:
            errors["vehicle_density"] = "must be at least 0"
        elif value > 500:
            errors["vehicle_density"] = "must be at most 500"
        else:
            data["vehicle_density"] = float(value)

    # avg_speed
    value = data.get("avg_speed")
    if value is not None and "avg_speed" not in errors:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors["avg_speed"] = "must be a number"
        elif value < 0:
            errors["avg_speed"] = "must be at least 0"
        elif value > 120:
            errors["avg_speed"] = "must be at most 120"
        else:
            data["avg_speed"] = float(value)

    # road_occupancy
    value = data.get("road_occupancy")
    if value is not None and "road_occupancy" not in errors:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors["road_occupancy"] = "must be a number"
        elif value < 0:
            errors["road_occupancy"] = "must be at least 0"
        elif value > 1:
            errors["road_occupancy"] = "must be at most 1"
        else:
            data["road_occupancy"] = float(value)

    # traffic_flow
    value = data.get("traffic_flow")
    if value is not None and "traffic_flow" not in errors:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors["traffic_flow"] = "must be a number"
        elif value < 0:
            errors["traffic_flow"] = "must be at least 0"
        elif value > 5000:
            errors["traffic_flow"] = "must be at most 5000"
        else:
            data["traffic_flow"] = float(value)

    # source
    value = data.get("source")
    if value is not None and "source" not in errors:
        if not isinstance(value, str):
            errors["source"] = "must be text"
        elif len(value) > 200:
            errors["source"] = "must be at most 200 characters"
        elif value not in SOURCE_CHOICES:
            errors["source"] = "must be one of: " + ", ".join(SOURCE_CHOICES)
        else:
            data["source"] = value.strip()

    if errors:
        raise ValidationError(errors)
    return data


def _check_references(conn: sqlite3.Connection, data: dict) -> None:
    errors: dict[str, str] = {}
    if data.get("stop_id") is not None and not stop_repo.exists(conn, data["stop_id"]):
        errors["stop_id"] = "stop not found"
    if errors:
        raise ValidationError(errors)


def _check_unique(conn: sqlite3.Connection, data: dict, current_id: Optional[int] = None) -> None:
    return None


def create(data: dict) -> TrafficReading:
    data = _validate(dict(data))
    with database.session() as conn:
        _check_references(conn, data)
        _check_unique(conn, data)
        try:
            return repo.create(conn, data)
        except sqlite3.IntegrityError as exc:
            raise ConflictError(str(exc)) from exc


def get(item_id: int) -> TrafficReading:
    with database.session() as conn:
        item = repo.get(conn, item_id)
    if item is None:
        raise NotFoundError(f"traffic reading {item_id} not found")
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


def update(item_id: int, changes: dict) -> TrafficReading:
    changes = _validate(dict(changes), partial=True)
    with database.session() as conn:
        current = repo.get(conn, item_id)
        if current is None:
            raise NotFoundError(f"traffic reading {item_id} not found")
        _check_references(conn, changes)
        _check_unique(conn, changes, current_id=item_id)
        try:
            return repo.update(conn, item_id, changes)
        except sqlite3.IntegrityError as exc:
            raise ConflictError(str(exc)) from exc


def delete(item_id: int) -> None:
    with database.session() as conn:
        if not repo.exists(conn, item_id):
            raise NotFoundError(f"traffic reading {item_id} not found")
        try:
            repo.delete(conn, item_id)
        except sqlite3.IntegrityError as exc:
            raise ConflictError("traffic reading is still referenced by other records") from exc


def bulk_create(items: list[dict]) -> list[TrafficReading]:
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
