"""Business rules for feedback: validation, reference checks, uniqueness."""
import csv
import io
import sqlite3
from datetime import datetime
from typing import Optional

from app import database
from app.errors import ConflictError, NotFoundError, ValidationError
from app.models.feedback import Feedback, FIELDS, CATEGORY_CHOICES
from app.repositories import feedback_repo as repo
from app.repositories import app_user_repo
from app.repositories import trip_repo

REQUIRED_FIELDS = ("rating",)
MAX_PAGE_SIZE = 500


def _is_blank(value) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _validate(data: dict, partial: bool = False) -> dict:
    """Check every field. With partial=True only the fields present are checked."""
    errors: dict[str, str] = {}
    for name in REQUIRED_FIELDS:
        if (not partial or name in data) and _is_blank(data.get(name)):
            errors[name] = "is required"

    # user_id
    value = data.get("user_id")
    if value is not None and "user_id" not in errors:
        if isinstance(value, bool) or not isinstance(value, int):
            errors["user_id"] = "must be a whole number"
        elif value < 1:
            errors["user_id"] = "must be a valid id"

    # trip_id
    value = data.get("trip_id")
    if value is not None and "trip_id" not in errors:
        if isinstance(value, bool) or not isinstance(value, int):
            errors["trip_id"] = "must be a whole number"
        elif value < 1:
            errors["trip_id"] = "must be a valid id"

    # rating
    value = data.get("rating")
    if value is not None and "rating" not in errors:
        if isinstance(value, bool) or not isinstance(value, int):
            errors["rating"] = "must be a whole number"
        elif value < 1:
            errors["rating"] = "must be at least 1"
        elif value > 5:
            errors["rating"] = "must be at most 5"

    # comfort_rating
    value = data.get("comfort_rating")
    if value is not None and "comfort_rating" not in errors:
        if isinstance(value, bool) or not isinstance(value, int):
            errors["comfort_rating"] = "must be a whole number"
        elif value < 1:
            errors["comfort_rating"] = "must be at least 1"
        elif value > 5:
            errors["comfort_rating"] = "must be at most 5"

    # category
    value = data.get("category")
    if value is not None and "category" not in errors:
        if not isinstance(value, str):
            errors["category"] = "must be text"
        elif len(value) > 200:
            errors["category"] = "must be at most 200 characters"
        elif value not in CATEGORY_CHOICES:
            errors["category"] = "must be one of: " + ", ".join(CATEGORY_CHOICES)
        else:
            data["category"] = value.strip()

    # comment
    value = data.get("comment")
    if value is not None and "comment" not in errors:
        if not isinstance(value, str):
            errors["comment"] = "must be text"
        elif len(value) > 2000:
            errors["comment"] = "must be at most 2000 characters"
        else:
            data["comment"] = value.strip()

    if errors:
        raise ValidationError(errors)
    return data


def _check_references(conn: sqlite3.Connection, data: dict) -> None:
    errors: dict[str, str] = {}
    if data.get("user_id") is not None and not app_user_repo.exists(conn, data["user_id"]):
        errors["user_id"] = "app user not found"
    if data.get("trip_id") is not None and not trip_repo.exists(conn, data["trip_id"]):
        errors["trip_id"] = "trip not found"
    if errors:
        raise ValidationError(errors)


def _check_unique(conn: sqlite3.Connection, data: dict, current_id: Optional[int] = None) -> None:
    return None


def create(data: dict) -> Feedback:
    data = _validate(dict(data))
    with database.session() as conn:
        _check_references(conn, data)
        _check_unique(conn, data)
        try:
            return repo.create(conn, data)
        except sqlite3.IntegrityError as exc:
            raise ConflictError(str(exc)) from exc


def get(item_id: int) -> Feedback:
    with database.session() as conn:
        item = repo.get(conn, item_id)
    if item is None:
        raise NotFoundError(f"feedback {item_id} not found")
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


def update(item_id: int, changes: dict) -> Feedback:
    changes = _validate(dict(changes), partial=True)
    with database.session() as conn:
        current = repo.get(conn, item_id)
        if current is None:
            raise NotFoundError(f"feedback {item_id} not found")
        _check_references(conn, changes)
        _check_unique(conn, changes, current_id=item_id)
        try:
            return repo.update(conn, item_id, changes)
        except sqlite3.IntegrityError as exc:
            raise ConflictError(str(exc)) from exc


def delete(item_id: int) -> None:
    with database.session() as conn:
        if not repo.exists(conn, item_id):
            raise NotFoundError(f"feedback {item_id} not found")
        try:
            repo.delete(conn, item_id)
        except sqlite3.IntegrityError as exc:
            raise ConflictError("feedback is still referenced by other records") from exc


def bulk_create(items: list[dict]) -> list[Feedback]:
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
