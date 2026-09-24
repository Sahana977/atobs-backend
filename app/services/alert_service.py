"""Business rules for alerts: validation, reference checks, uniqueness."""
import csv
import io
import sqlite3
from datetime import datetime
from typing import Optional

from app import database
from app.errors import ConflictError, NotFoundError, ValidationError
from app.models.alert import Alert, FIELDS, SEVERITY_CHOICES
from app.repositories import alert_repo as repo
from app.repositories import route_repo
from app.repositories import stop_repo

REQUIRED_FIELDS = ("title", "message", "starts_at",)
MAX_PAGE_SIZE = 500


def _is_blank(value) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _validate(data: dict, partial: bool = False) -> dict:
    """Check every field. With partial=True only the fields present are checked."""
    errors: dict[str, str] = {}
    for name in REQUIRED_FIELDS:
        if (not partial or name in data) and _is_blank(data.get(name)):
            errors[name] = "is required"

    # title
    value = data.get("title")
    if value is not None and "title" not in errors:
        if not isinstance(value, str):
            errors["title"] = "must be text"
        elif len(value) > 200:
            errors["title"] = "must be at most 200 characters"
        else:
            data["title"] = value.strip()

    # message
    value = data.get("message")
    if value is not None and "message" not in errors:
        if not isinstance(value, str):
            errors["message"] = "must be text"
        elif len(value) > 2000:
            errors["message"] = "must be at most 2000 characters"
        else:
            data["message"] = value.strip()

    # severity
    value = data.get("severity")
    if value is not None and "severity" not in errors:
        if not isinstance(value, str):
            errors["severity"] = "must be text"
        elif len(value) > 200:
            errors["severity"] = "must be at most 200 characters"
        elif value not in SEVERITY_CHOICES:
            errors["severity"] = "must be one of: " + ", ".join(SEVERITY_CHOICES)
        else:
            data["severity"] = value.strip()

    # stop_id
    value = data.get("stop_id")
    if value is not None and "stop_id" not in errors:
        if isinstance(value, bool) or not isinstance(value, int):
            errors["stop_id"] = "must be a whole number"
        elif value < 1:
            errors["stop_id"] = "must be a valid id"

    # route_id
    value = data.get("route_id")
    if value is not None and "route_id" not in errors:
        if isinstance(value, bool) or not isinstance(value, int):
            errors["route_id"] = "must be a whole number"
        elif value < 1:
            errors["route_id"] = "must be a valid id"

    # starts_at
    value = data.get("starts_at")
    if value is not None and "starts_at" not in errors:
        if not isinstance(value, str):
            errors["starts_at"] = "must be an ISO date-time string"
        else:
            try:
                data["starts_at"] = datetime.fromisoformat(value).isoformat(timespec="seconds")
            except ValueError:
                errors["starts_at"] = "must be an ISO date-time like 2026-10-01T08:30:00"

    # ends_at
    value = data.get("ends_at")
    if value is not None and "ends_at" not in errors:
        if not isinstance(value, str):
            errors["ends_at"] = "must be an ISO date-time string"
        else:
            try:
                data["ends_at"] = datetime.fromisoformat(value).isoformat(timespec="seconds")
            except ValueError:
                errors["ends_at"] = "must be an ISO date-time like 2026-10-01T08:30:00"

    # is_active
    value = data.get("is_active")
    if value is not None and "is_active" not in errors:
        if not isinstance(value, bool):
            errors["is_active"] = "must be true or false"

    # cross-field rules
    start, end = data.get("starts_at"), data.get("ends_at")
    if "starts_at" not in errors and "ends_at" not in errors and start and end and end <= start:
        errors["ends_at"] = "must be after starts_at"

    if errors:
        raise ValidationError(errors)
    return data


def _check_references(conn: sqlite3.Connection, data: dict) -> None:
    errors: dict[str, str] = {}
    if data.get("stop_id") is not None and not stop_repo.exists(conn, data["stop_id"]):
        errors["stop_id"] = "stop not found"
    if data.get("route_id") is not None and not route_repo.exists(conn, data["route_id"]):
        errors["route_id"] = "route not found"
    if errors:
        raise ValidationError(errors)


def _check_unique(conn: sqlite3.Connection, data: dict, current_id: Optional[int] = None) -> None:
    return None


def create(data: dict) -> Alert:
    data = _validate(dict(data))
    with database.session() as conn:
        _check_references(conn, data)
        _check_unique(conn, data)
        try:
            return repo.create(conn, data)
        except sqlite3.IntegrityError as exc:
            raise ConflictError(str(exc)) from exc


def get(item_id: int) -> Alert:
    with database.session() as conn:
        item = repo.get(conn, item_id)
    if item is None:
        raise NotFoundError(f"alert {item_id} not found")
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


def update(item_id: int, changes: dict) -> Alert:
    changes = _validate(dict(changes), partial=True)
    with database.session() as conn:
        current = repo.get(conn, item_id)
        if current is None:
            raise NotFoundError(f"alert {item_id} not found")
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
            raise NotFoundError(f"alert {item_id} not found")
        try:
            repo.delete(conn, item_id)
        except sqlite3.IntegrityError as exc:
            raise ConflictError("alert is still referenced by other records") from exc


def bulk_create(items: list[dict]) -> list[Alert]:
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
