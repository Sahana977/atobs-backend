"""Data access for route stops — plain SQL on sqlite3, no ORM."""
import sqlite3
from typing import Optional

from app.models.route_stop import COLUMNS, TABLE, RouteStop
from app.utils.time_utils import now_iso

SORTABLE = set(COLUMNS)


def _to_db_bool(value):
    return None if value is None else int(bool(value))


def create(conn: sqlite3.Connection, data: dict) -> RouteStop:
    ts = now_iso()
    cur = conn.execute(
        "INSERT INTO route_stops ("
        "route_id, stop_id, sequence, minutes_from_start, created_at, updated_at"
        ") VALUES (?, ?, ?, ?, ?, ?)",
        (
            data.get("route_id"),
            data.get("stop_id"),
            data.get("sequence"),
            data.get("minutes_from_start", 0.0),
            ts,
            ts,
        ),
    )
    return get(conn, cur.lastrowid)


def get(conn: sqlite3.Connection, item_id: int) -> Optional[RouteStop]:
    row = conn.execute("SELECT * FROM route_stops WHERE id = ?", (item_id,)).fetchone()
    return RouteStop.from_row(row) if row else None


def exists(conn: sqlite3.Connection, item_id: int) -> bool:
    return conn.execute("SELECT 1 FROM route_stops WHERE id = ?", (item_id,)).fetchone() is not None


def _where(filters: Optional[dict]) -> tuple[str, list]:
    filters = filters or {}
    clauses: list[str] = []
    params: list = []
    if filters.get("route_id") is not None:
        clauses.append("route_id = ?")
        params.append(filters["route_id"])
    if filters.get("stop_id") is not None:
        clauses.append("stop_id = ?")
        params.append(filters["stop_id"])
    if filters.get("min_sequence") is not None:
        clauses.append("sequence >= ?")
        params.append(filters["min_sequence"])
    if filters.get("max_sequence") is not None:
        clauses.append("sequence <= ?")
        params.append(filters["max_sequence"])
    if filters.get("min_minutes_from_start") is not None:
        clauses.append("minutes_from_start >= ?")
        params.append(filters["min_minutes_from_start"])
    if filters.get("max_minutes_from_start") is not None:
        clauses.append("minutes_from_start <= ?")
        params.append(filters["max_minutes_from_start"])
    sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return sql, params


def list_(conn: sqlite3.Connection, filters: Optional[dict] = None, limit: int = 50, offset: int = 0,
          order_by: str = "id", descending: bool = False) -> list[RouteStop]:
    if order_by not in SORTABLE:
        order_by = "id"
    where, params = _where(filters)
    direction = "DESC" if descending else "ASC"
    sql = f"SELECT * FROM route_stops{where} ORDER BY {order_by} {direction} LIMIT ? OFFSET ?"
    rows = conn.execute(sql, [*params, limit, offset]).fetchall()
    return [RouteStop.from_row(r) for r in rows]


def count(conn: sqlite3.Connection, filters: Optional[dict] = None) -> int:
    where, params = _where(filters)
    return conn.execute(f"SELECT COUNT(*) FROM route_stops{where}", params).fetchone()[0]


def update(conn: sqlite3.Connection, item_id: int, changes: dict) -> Optional[RouteStop]:
    allowed = {}
    if changes.get("route_id") is not None:
        allowed["route_id"] = changes["route_id"]
    if changes.get("stop_id") is not None:
        allowed["stop_id"] = changes["stop_id"]
    if changes.get("sequence") is not None:
        allowed["sequence"] = changes["sequence"]
    if changes.get("minutes_from_start") is not None:
        allowed["minutes_from_start"] = changes["minutes_from_start"]
    if not allowed:
        return get(conn, item_id)
    assignments = ", ".join(f"{column} = ?" for column in allowed)
    conn.execute(
        f"UPDATE route_stops SET {assignments}, updated_at = ? WHERE id = ?",
        [*allowed.values(), now_iso(), item_id],
    )
    return get(conn, item_id)


def delete(conn: sqlite3.Connection, item_id: int) -> bool:
    cur = conn.execute("DELETE FROM route_stops WHERE id = ?", (item_id,))
    return cur.rowcount > 0


def bulk_create(conn: sqlite3.Connection, items: list[dict]) -> list[RouteStop]:
    return [create(conn, item) for item in items]
