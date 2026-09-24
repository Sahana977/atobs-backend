"""Data access for routes — plain SQL on sqlite3, no ORM."""
import sqlite3
from typing import Optional

from app.models.route import COLUMNS, TABLE, Route
from app.utils.time_utils import now_iso

SORTABLE = set(COLUMNS)


def _to_db_bool(value):
    return None if value is None else int(bool(value))


def create(conn: sqlite3.Connection, data: dict) -> Route:
    ts = now_iso()
    cur = conn.execute(
        "INSERT INTO routes ("
        "route_number, name, origin_stop_id, destination_stop_id, distance_km, service_type, avg_headway_min, is_active, created_at, updated_at"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            data.get("route_number"),
            data.get("name"),
            data.get("origin_stop_id"),
            data.get("destination_stop_id"),
            data.get("distance_km"),
            data.get("service_type", 'ordinary'),
            data.get("avg_headway_min", 15),
            _to_db_bool(data.get("is_active", True)),
            ts,
            ts,
        ),
    )
    return get(conn, cur.lastrowid)


def get(conn: sqlite3.Connection, item_id: int) -> Optional[Route]:
    row = conn.execute("SELECT * FROM routes WHERE id = ?", (item_id,)).fetchone()
    return Route.from_row(row) if row else None


def get_by_route_number(conn: sqlite3.Connection, value) -> Optional[Route]:
    row = conn.execute("SELECT * FROM routes WHERE route_number = ?", (value,)).fetchone()
    return Route.from_row(row) if row else None


def exists(conn: sqlite3.Connection, item_id: int) -> bool:
    return conn.execute("SELECT 1 FROM routes WHERE id = ?", (item_id,)).fetchone() is not None


def _where(filters: Optional[dict]) -> tuple[str, list]:
    filters = filters or {}
    clauses: list[str] = []
    params: list = []
    if filters.get("route_number") is not None:
        clauses.append("route_number = ?")
        params.append(filters["route_number"])
    if filters.get("origin_stop_id") is not None:
        clauses.append("origin_stop_id = ?")
        params.append(filters["origin_stop_id"])
    if filters.get("destination_stop_id") is not None:
        clauses.append("destination_stop_id = ?")
        params.append(filters["destination_stop_id"])
    if filters.get("min_distance_km") is not None:
        clauses.append("distance_km >= ?")
        params.append(filters["min_distance_km"])
    if filters.get("max_distance_km") is not None:
        clauses.append("distance_km <= ?")
        params.append(filters["max_distance_km"])
    if filters.get("service_type") is not None:
        clauses.append("service_type = ?")
        params.append(filters["service_type"])
    if filters.get("min_avg_headway_min") is not None:
        clauses.append("avg_headway_min >= ?")
        params.append(filters["min_avg_headway_min"])
    if filters.get("max_avg_headway_min") is not None:
        clauses.append("avg_headway_min <= ?")
        params.append(filters["max_avg_headway_min"])
    if filters.get("is_active") is not None:
        clauses.append("is_active = ?")
        params.append(_to_db_bool(filters["is_active"]))
    if filters.get("q"):
        clauses.append("(name LIKE ?)")
        like = f"%{filters['q']}%"
        params.extend([like] * 1)
    sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return sql, params


def list_(conn: sqlite3.Connection, filters: Optional[dict] = None, limit: int = 50, offset: int = 0,
          order_by: str = "id", descending: bool = False) -> list[Route]:
    if order_by not in SORTABLE:
        order_by = "id"
    where, params = _where(filters)
    direction = "DESC" if descending else "ASC"
    sql = f"SELECT * FROM routes{where} ORDER BY {order_by} {direction} LIMIT ? OFFSET ?"
    rows = conn.execute(sql, [*params, limit, offset]).fetchall()
    return [Route.from_row(r) for r in rows]


def count(conn: sqlite3.Connection, filters: Optional[dict] = None) -> int:
    where, params = _where(filters)
    return conn.execute(f"SELECT COUNT(*) FROM routes{where}", params).fetchone()[0]


def update(conn: sqlite3.Connection, item_id: int, changes: dict) -> Optional[Route]:
    allowed = {}
    if changes.get("route_number") is not None:
        allowed["route_number"] = changes["route_number"]
    if changes.get("name") is not None:
        allowed["name"] = changes["name"]
    if changes.get("origin_stop_id") is not None:
        allowed["origin_stop_id"] = changes["origin_stop_id"]
    if changes.get("destination_stop_id") is not None:
        allowed["destination_stop_id"] = changes["destination_stop_id"]
    if changes.get("distance_km") is not None:
        allowed["distance_km"] = changes["distance_km"]
    if changes.get("service_type") is not None:
        allowed["service_type"] = changes["service_type"]
    if changes.get("avg_headway_min") is not None:
        allowed["avg_headway_min"] = changes["avg_headway_min"]
    if changes.get("is_active") is not None:
        allowed["is_active"] = _to_db_bool(changes["is_active"])
    if not allowed:
        return get(conn, item_id)
    assignments = ", ".join(f"{column} = ?" for column in allowed)
    conn.execute(
        f"UPDATE routes SET {assignments}, updated_at = ? WHERE id = ?",
        [*allowed.values(), now_iso(), item_id],
    )
    return get(conn, item_id)


def delete(conn: sqlite3.Connection, item_id: int) -> bool:
    cur = conn.execute("DELETE FROM routes WHERE id = ?", (item_id,))
    return cur.rowcount > 0


def bulk_create(conn: sqlite3.Connection, items: list[dict]) -> list[Route]:
    return [create(conn, item) for item in items]
