"""Data access for feedback — plain SQL on sqlite3, no ORM."""
import sqlite3
from typing import Optional

from app.models.feedback import COLUMNS, TABLE, Feedback
from app.utils.time_utils import now_iso

SORTABLE = set(COLUMNS)


def _to_db_bool(value):
    return None if value is None else int(bool(value))


def create(conn: sqlite3.Connection, data: dict) -> Feedback:
    ts = now_iso()
    cur = conn.execute(
        "INSERT INTO feedback ("
        "user_id, trip_id, rating, comfort_rating, category, comment, created_at, updated_at"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            data.get("user_id"),
            data.get("trip_id"),
            data.get("rating"),
            data.get("comfort_rating"),
            data.get("category", 'other'),
            data.get("comment"),
            ts,
            ts,
        ),
    )
    return get(conn, cur.lastrowid)


def get(conn: sqlite3.Connection, item_id: int) -> Optional[Feedback]:
    row = conn.execute("SELECT * FROM feedback WHERE id = ?", (item_id,)).fetchone()
    return Feedback.from_row(row) if row else None


def exists(conn: sqlite3.Connection, item_id: int) -> bool:
    return conn.execute("SELECT 1 FROM feedback WHERE id = ?", (item_id,)).fetchone() is not None


def _where(filters: Optional[dict]) -> tuple[str, list]:
    filters = filters or {}
    clauses: list[str] = []
    params: list = []
    if filters.get("user_id") is not None:
        clauses.append("user_id = ?")
        params.append(filters["user_id"])
    if filters.get("trip_id") is not None:
        clauses.append("trip_id = ?")
        params.append(filters["trip_id"])
    if filters.get("min_rating") is not None:
        clauses.append("rating >= ?")
        params.append(filters["min_rating"])
    if filters.get("max_rating") is not None:
        clauses.append("rating <= ?")
        params.append(filters["max_rating"])
    if filters.get("min_comfort_rating") is not None:
        clauses.append("comfort_rating >= ?")
        params.append(filters["min_comfort_rating"])
    if filters.get("max_comfort_rating") is not None:
        clauses.append("comfort_rating <= ?")
        params.append(filters["max_comfort_rating"])
    if filters.get("category") is not None:
        clauses.append("category = ?")
        params.append(filters["category"])
    if filters.get("q"):
        clauses.append("(comment LIKE ?)")
        like = f"%{filters['q']}%"
        params.extend([like] * 1)
    sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return sql, params


def list_(conn: sqlite3.Connection, filters: Optional[dict] = None, limit: int = 50, offset: int = 0,
          order_by: str = "id", descending: bool = False) -> list[Feedback]:
    if order_by not in SORTABLE:
        order_by = "id"
    where, params = _where(filters)
    direction = "DESC" if descending else "ASC"
    sql = f"SELECT * FROM feedback{where} ORDER BY {order_by} {direction} LIMIT ? OFFSET ?"
    rows = conn.execute(sql, [*params, limit, offset]).fetchall()
    return [Feedback.from_row(r) for r in rows]


def count(conn: sqlite3.Connection, filters: Optional[dict] = None) -> int:
    where, params = _where(filters)
    return conn.execute(f"SELECT COUNT(*) FROM feedback{where}", params).fetchone()[0]


def update(conn: sqlite3.Connection, item_id: int, changes: dict) -> Optional[Feedback]:
    allowed = {}
    if changes.get("user_id") is not None:
        allowed["user_id"] = changes["user_id"]
    if changes.get("trip_id") is not None:
        allowed["trip_id"] = changes["trip_id"]
    if changes.get("rating") is not None:
        allowed["rating"] = changes["rating"]
    if changes.get("comfort_rating") is not None:
        allowed["comfort_rating"] = changes["comfort_rating"]
    if changes.get("category") is not None:
        allowed["category"] = changes["category"]
    if changes.get("comment") is not None:
        allowed["comment"] = changes["comment"]
    if not allowed:
        return get(conn, item_id)
    assignments = ", ".join(f"{column} = ?" for column in allowed)
    conn.execute(
        f"UPDATE feedback SET {assignments}, updated_at = ? WHERE id = ?",
        [*allowed.values(), now_iso(), item_id],
    )
    return get(conn, item_id)


def delete(conn: sqlite3.Connection, item_id: int) -> bool:
    cur = conn.execute("DELETE FROM feedback WHERE id = ?", (item_id,))
    return cur.rowcount > 0


def bulk_create(conn: sqlite3.Connection, items: list[dict]) -> list[Feedback]:
    return [create(conn, item) for item in items]
