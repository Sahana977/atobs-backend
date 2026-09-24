"""Business rules for occupancy readings: validation, reference checks, uniqueness."""
import csv
import io
import sqlite3
from datetime import datetime
from typing import Optional

from app import database
from app.errors import ConflictError, NotFoundError, ValidationError
from app.models.occupancy_reading import OccupancyReading, FIELDS, SOURCE_CHOICES
from app.repositories import occupancy_reading_repo as repo
from app.repositories import stop_repo
from app.repositories import trip_repo

REQUIRED_FIELDS = ("trip_id", "stop_id", "recorded_at", "passengers_on_board", "occupancy_pct",)
MAX_PAGE_SIZE = 500


def _is_blank(value) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _validate(data: dict, partial: bool = False) -> dict:
    """Check every field. With partial=True only the fields present are checked."""
    errors: dict[str, str] = {}
    for name in REQUIRED_FIELDS:
        if (not partial or name in data) and _is_blank(data.get(name)):
            errors[name] = "is required"

    # trip_id
    value = data.get("trip_id")
    if value is not None and "trip_id" not in errors:
        if isinstance(value, bool) or not isinstance(value, int):
            errors["trip_id"] = "must be a whole number"
        elif value < 1:
            errors["trip_id"] = "must be a valid id"

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

    # passengers_on_board
    value = data.get("passengers_on_board")
    if value is not None and "passengers_on_board" not in errors:
        if isinstance(value, bool) or not isinstance(value, int):
            errors["passengers_on_board"] = "must be a whole number"
        elif value < 0:
            errors["passengers_on_board"] = "must be at least 0"
        elif value > 300:
            errors["passengers_on_board"] = "must be at most 300"

    # occupancy_pct
    value = data.get("occupancy_pct")
    if value is not None and "occupancy_pct" not in errors:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors["occupancy_pct"] = "must be a number"
        elif value < 0:
            errors["occupancy_pct"] = "must be at least 0"
        elif value > 200:
            errors["occupancy_pct"] = "must be at most 200"
        else:
            data["occupancy_pct"] = float(value)

    # delay_min
    value = data.get("delay_min")
    if value is not None and "delay_min" not in errors:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors["delay_min"] = "must be a number"
        elif value < 0:
            errors["delay_min"] = "must be at least 0"
        elif value > 180:
            errors["delay_min"] = "must be at most 180"
        else:
            data["delay_min"] = float(value)

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
    if data.get("trip_id") is not None and not trip_repo.exists(conn, data["trip_id"]):
        errors["trip_id"] = "trip not found"
    if data.get("stop_id") is not None and not stop_repo.exists(conn, data["stop_id"]):
        errors["stop_id"] = "stop not found"
    if errors:
        raise ValidationError(errors)


def _check_unique(conn: sqlite3.Connection, data: dict, current_id: Optional[int] = None) -> None:
    return None


def create(data: dict) -> OccupancyReading:
    data = _validate(dict(data))
    with database.session() as conn:
        _check_references(conn, data)
        _check_unique(conn, data)
        try:
            return repo.create(conn, data)
        except sqlite3.IntegrityError as exc:
            raise ConflictError(str(exc)) from exc


def get(item_id: int) -> OccupancyReading:
    with database.session() as conn:
        item = repo.get(conn, item_id)
    if item is None:
        raise NotFoundError(f"occupancy reading {item_id} not found")
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


def update(item_id: int, changes: dict) -> OccupancyReading:
    changes = _validate(dict(changes), partial=True)
    with database.session() as conn:
        current = repo.get(conn, item_id)
        if current is None:
            raise NotFoundError(f"occupancy reading {item_id} not found")
        _check_references(conn, changes)
        _check_unique(conn, changes, current_id=item_id)
        try:
            return repo.update(conn, item_id, changes)
        except sqlite3.IntegrityError as exc:
            raise ConflictError(str(exc)) from exc


def delete(item_id: int) -> None:
    with database.session() as conn:
        if not repo.exists(conn, item_id):
            raise NotFoundError(f"occupancy reading {item_id} not found")
        try:
            repo.delete(conn, item_id)
        except sqlite3.IntegrityError as exc:
            raise ConflictError("occupancy reading is still referenced by other records") from exc


def bulk_create(items: list[dict]) -> list[OccupancyReading]:
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
