"""Data access for depots — plain SQL on sqlite3, no ORM."""
import sqlite3
from typing import Optional

from app.models.depot import COLUMNS, TABLE, Depot
from app.utils.time_utils import now_iso

SORTABLE = set(COLUMNS)


def _to_db_bool(value):
    return None if value is None else int(bool(value))


def create(conn: sqlite3.Connection, data: dict) -> Depot:
    ts = now_iso()
    cur = conn.execute(
        "INSERT INTO depots ("
        "depot_code, name, area, capacity, latitude, longitude, is_active, created_at, updated_at"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            data.get("depot_code"),
            data.get("name"),
            data.get("area"),
            data.get("capacity", 100),
            data.get("latitude"),
            data.get("longitude"),
            _to_db_bool(data.get("is_active", True)),
            ts,
            ts,
        ),
    )
    return get(conn, cur.lastrowid)


def get(conn: sqlite3.Connection, item_id: int) -> Optional[Depot]:
    row = conn.execute("SELECT * FROM depots WHERE id = ?", (item_id,)).fetchone()
    return Depot.from_row(row) if row else None


def get_by_depot_code(conn: sqlite3.Connection, value) -> Optional[Depot]:
    row = conn.execute("SELECT * FROM depots WHERE depot_code = ?", (value,)).fetchone()
    return Depot.from_row(row) if row else None


def exists(conn: sqlite3.Connection, item_id: int) -> bool:
    return conn.execute("SELECT 1 FROM depots WHERE id = ?", (item_id,)).fetchone() is not None


def _where(filters: Optional[dict]) -> tuple[str, list]:
    filters = filters or {}
    clauses: list[str] = []
    params: list = []
    if filters.get("depot_code") is not None:
        clauses.append("depot_code = ?")
        params.append(filters["depot_code"])
    if filters.get("min_capacity") is not None:
        clauses.append("capacity >= ?")
        params.append(filters["min_capacity"])
    if filters.get("max_capacity") is not None:
        clauses.append("capacity <= ?")
        params.append(filters["max_capacity"])
    if filters.get("min_latitude") is not None:
        clauses.append("latitude >= ?")
        params.append(filters["min_latitude"])
    if filters.get("max_latitude") is not None:
        clauses.append("latitude <= ?")
        params.append(filters["max_latitude"])
    if filters.get("min_longitude") is not None:
        clauses.append("longitude >= ?")
        params.append(filters["min_longitude"])
    if filters.get("max_longitude") is not None:
        clauses.append("longitude <= ?")
        params.append(filters["max_longitude"])
    if filters.get("is_active") is not None:
        clauses.append("is_active = ?")
        params.append(_to_db_bool(filters["is_active"]))
    if filters.get("q"):
        clauses.append("(name LIKE ? OR area LIKE ?)")
        like = f"%{filters['q']}%"
        params.extend([like] * 2)
    sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return sql, params


def list_(conn: sqlite3.Connection, filters: Optional[dict] = None, limit: int = 50, offset: int = 0,
          order_by: str = "id", descending: bool = False) -> list[Depot]:
    if order_by not in SORTABLE:
        order_by = "id"
    where, params = _where(filters)
    direction = "DESC" if descending else "ASC"
    sql = f"SELECT * FROM depots{where} ORDER BY {order_by} {direction} LIMIT ? OFFSET ?"
    rows = conn.execute(sql, [*params, limit, offset]).fetchall()
    return [Depot.from_row(r) for r in rows]


def count(conn: sqlite3.Connection, filters: Optional[dict] = None) -> int:
    where, params = _where(filters)
    return conn.execute(f"SELECT COUNT(*) FROM depots{where}", params).fetchone()[0]


def update(conn: sqlite3.Connection, item_id: int, changes: dict) -> Optional[Depot]:
    allowed = {}
    if changes.get("depot_code") is not None:
        allowed["depot_code"] = changes["depot_code"]
    if changes.get("name") is not None:
        allowed["name"] = changes["name"]
    if changes.get("area") is not None:
        allowed["area"] = changes["area"]
    if changes.get("capacity") is not None:
        allowed["capacity"] = changes["capacity"]
    if changes.get("latitude") is not None:
        allowed["latitude"] = changes["latitude"]
    if changes.get("longitude") is not None:
        allowed["longitude"] = changes["longitude"]
    if changes.get("is_active") is not None:
        allowed["is_active"] = _to_db_bool(changes["is_active"])
    if not allowed:
        return get(conn, item_id)
    assignments = ", ".join(f"{column} = ?" for column in allowed)
    conn.execute(
        f"UPDATE depots SET {assignments}, updated_at = ? WHERE id = ?",
        [*allowed.values(), now_iso(), item_id],
    )
    return get(conn, item_id)


def delete(conn: sqlite3.Connection, item_id: int) -> bool:
    cur = conn.execute("DELETE FROM depots WHERE id = ?", (item_id,))
    return cur.rowcount > 0


def bulk_create(conn: sqlite3.Connection, items: list[dict]) -> list[Depot]:
    return [create(conn, item) for item in items]
