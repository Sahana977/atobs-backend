"""Data access for trips — plain SQL on sqlite3, no ORM."""
import sqlite3
from typing import Optional

from app.models.trip import COLUMNS, TABLE, Trip
from app.utils.time_utils import now_iso

SORTABLE = set(COLUMNS)


def _to_db_bool(value):
    return None if value is None else int(bool(value))


def create(conn: sqlite3.Connection, data: dict) -> Trip:
    ts = now_iso()
    cur = conn.execute(
        "INSERT INTO trips ("
        "trip_code, route_id, bus_id, scheduled_start, scheduled_end, status, created_at, updated_at"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            data.get("trip_code"),
            data.get("route_id"),
            data.get("bus_id"),
            data.get("scheduled_start"),
            data.get("scheduled_end"),
            data.get("status", 'scheduled'),
            ts,
            ts,
        ),
    )
    return get(conn, cur.lastrowid)


def get(conn: sqlite3.Connection, item_id: int) -> Optional[Trip]:
    row = conn.execute("SELECT * FROM trips WHERE id = ?", (item_id,)).fetchone()
    return Trip.from_row(row) if row else None


def get_by_trip_code(conn: sqlite3.Connection, value) -> Optional[Trip]:
    row = conn.execute("SELECT * FROM trips WHERE trip_code = ?", (value,)).fetchone()
    return Trip.from_row(row) if row else None


def exists(conn: sqlite3.Connection, item_id: int) -> bool:
    return conn.execute("SELECT 1 FROM trips WHERE id = ?", (item_id,)).fetchone() is not None


def _where(filters: Optional[dict]) -> tuple[str, list]:
    filters = filters or {}
    clauses: list[str] = []
    params: list = []
    if filters.get("trip_code") is not None:
        clauses.append("trip_code = ?")
        params.append(filters["trip_code"])
    if filters.get("route_id") is not None:
        clauses.append("route_id = ?")
        params.append(filters["route_id"])
    if filters.get("bus_id") is not None:
        clauses.append("bus_id = ?")
        params.append(filters["bus_id"])
    if filters.get("scheduled_start_from") is not None:
        clauses.append("scheduled_start >= ?")
        params.append(filters["scheduled_start_from"])
    if filters.get("scheduled_start_to") is not None:
        clauses.append("scheduled_start <= ?")
        params.append(filters["scheduled_start_to"])
    if filters.get("scheduled_end_from") is not None:
        clauses.append("scheduled_end >= ?")
        params.append(filters["scheduled_end_from"])
    if filters.get("scheduled_end_to") is not None:
        clauses.append("scheduled_end <= ?")
        params.append(filters["scheduled_end_to"])
    if filters.get("status") is not None:
        clauses.append("status = ?")
        params.append(filters["status"])
    sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return sql, params


def list_(conn: sqlite3.Connection, filters: Optional[dict] = None, limit: int = 50, offset: int = 0,
          order_by: str = "id", descending: bool = False) -> list[Trip]:
    if order_by not in SORTABLE:
        order_by = "id"
    where, params = _where(filters)
    direction = "DESC" if descending else "ASC"
    sql = f"SELECT * FROM trips{where} ORDER BY {order_by} {direction} LIMIT ? OFFSET ?"
    rows = conn.execute(sql, [*params, limit, offset]).fetchall()
    return [Trip.from_row(r) for r in rows]


def count(conn: sqlite3.Connection, filters: Optional[dict] = None) -> int:
    where, params = _where(filters)
    return conn.execute(f"SELECT COUNT(*) FROM trips{where}", params).fetchone()[0]


def update(conn: sqlite3.Connection, item_id: int, changes: dict) -> Optional[Trip]:
    allowed = {}
    if changes.get("trip_code") is not None:
        allowed["trip_code"] = changes["trip_code"]
    if changes.get("route_id") is not None:
        allowed["route_id"] = changes["route_id"]
    if changes.get("bus_id") is not None:
        allowed["bus_id"] = changes["bus_id"]
    if changes.get("scheduled_start") is not None:
        allowed["scheduled_start"] = changes["scheduled_start"]
    if changes.get("scheduled_end") is not None:
        allowed["scheduled_end"] = changes["scheduled_end"]
    if changes.get("status") is not None:
        allowed["status"] = changes["status"]
    if not allowed:
        return get(conn, item_id)
    assignments = ", ".join(f"{column} = ?" for column in allowed)
    conn.execute(
        f"UPDATE trips SET {assignments}, updated_at = ? WHERE id = ?",
        [*allowed.values(), now_iso(), item_id],
    )
    return get(conn, item_id)


def delete(conn: sqlite3.Connection, item_id: int) -> bool:
    cur = conn.execute("DELETE FROM trips WHERE id = ?", (item_id,))
    return cur.rowcount > 0


def bulk_create(conn: sqlite3.Connection, items: list[dict]) -> list[Trip]:
    return [create(conn, item) for item in items]
