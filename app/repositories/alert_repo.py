"""Data access for alerts — plain SQL on sqlite3, no ORM."""
import sqlite3
from typing import Optional

from app.models.alert import COLUMNS, TABLE, Alert
from app.utils.time_utils import now_iso

SORTABLE = set(COLUMNS)


def _to_db_bool(value):
    return None if value is None else int(bool(value))


def create(conn: sqlite3.Connection, data: dict) -> Alert:
    ts = now_iso()
    cur = conn.execute(
        "INSERT INTO alerts ("
        "title, message, severity, stop_id, route_id, starts_at, ends_at, is_active, created_at, updated_at"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            data.get("title"),
            data.get("message"),
            data.get("severity", 'info'),
            data.get("stop_id"),
            data.get("route_id"),
            data.get("starts_at"),
            data.get("ends_at"),
            _to_db_bool(data.get("is_active", True)),
            ts,
            ts,
        ),
    )
    return get(conn, cur.lastrowid)


def get(conn: sqlite3.Connection, item_id: int) -> Optional[Alert]:
    row = conn.execute("SELECT * FROM alerts WHERE id = ?", (item_id,)).fetchone()
    return Alert.from_row(row) if row else None


def exists(conn: sqlite3.Connection, item_id: int) -> bool:
    return conn.execute("SELECT 1 FROM alerts WHERE id = ?", (item_id,)).fetchone() is not None


def _where(filters: Optional[dict]) -> tuple[str, list]:
    filters = filters or {}
    clauses: list[str] = []
    params: list = []
    if filters.get("severity") is not None:
        clauses.append("severity = ?")
        params.append(filters["severity"])
    if filters.get("stop_id") is not None:
        clauses.append("stop_id = ?")
        params.append(filters["stop_id"])
    if filters.get("route_id") is not None:
        clauses.append("route_id = ?")
        params.append(filters["route_id"])
    if filters.get("starts_at_from") is not None:
        clauses.append("starts_at >= ?")
        params.append(filters["starts_at_from"])
    if filters.get("starts_at_to") is not None:
        clauses.append("starts_at <= ?")
        params.append(filters["starts_at_to"])
    if filters.get("ends_at_from") is not None:
        clauses.append("ends_at >= ?")
        params.append(filters["ends_at_from"])
    if filters.get("ends_at_to") is not None:
        clauses.append("ends_at <= ?")
        params.append(filters["ends_at_to"])
    if filters.get("is_active") is not None:
        clauses.append("is_active = ?")
        params.append(_to_db_bool(filters["is_active"]))
    if filters.get("q"):
        clauses.append("(title LIKE ? OR message LIKE ?)")
        like = f"%{filters['q']}%"
        params.extend([like] * 2)
    sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return sql, params


def list_(conn: sqlite3.Connection, filters: Optional[dict] = None, limit: int = 50, offset: int = 0,
          order_by: str = "id", descending: bool = False) -> list[Alert]:
    if order_by not in SORTABLE:
        order_by = "id"
    where, params = _where(filters)
    direction = "DESC" if descending else "ASC"
    sql = f"SELECT * FROM alerts{where} ORDER BY {order_by} {direction} LIMIT ? OFFSET ?"
    rows = conn.execute(sql, [*params, limit, offset]).fetchall()
    return [Alert.from_row(r) for r in rows]


def count(conn: sqlite3.Connection, filters: Optional[dict] = None) -> int:
    where, params = _where(filters)
    return conn.execute(f"SELECT COUNT(*) FROM alerts{where}", params).fetchone()[0]


def update(conn: sqlite3.Connection, item_id: int, changes: dict) -> Optional[Alert]:
    allowed = {}
    if changes.get("title") is not None:
        allowed["title"] = changes["title"]
    if changes.get("message") is not None:
        allowed["message"] = changes["message"]
    if changes.get("severity") is not None:
        allowed["severity"] = changes["severity"]
    if changes.get("stop_id") is not None:
        allowed["stop_id"] = changes["stop_id"]
    if changes.get("route_id") is not None:
        allowed["route_id"] = changes["route_id"]
    if changes.get("starts_at") is not None:
        allowed["starts_at"] = changes["starts_at"]
    if changes.get("ends_at") is not None:
        allowed["ends_at"] = changes["ends_at"]
    if changes.get("is_active") is not None:
        allowed["is_active"] = _to_db_bool(changes["is_active"])
    if not allowed:
        return get(conn, item_id)
    assignments = ", ".join(f"{column} = ?" for column in allowed)
    conn.execute(
        f"UPDATE alerts SET {assignments}, updated_at = ? WHERE id = ?",
        [*allowed.values(), now_iso(), item_id],
    )
    return get(conn, item_id)


def delete(conn: sqlite3.Connection, item_id: int) -> bool:
    cur = conn.execute("DELETE FROM alerts WHERE id = ?", (item_id,))
    return cur.rowcount > 0


def bulk_create(conn: sqlite3.Connection, items: list[dict]) -> list[Alert]:
    return [create(conn, item) for item in items]
