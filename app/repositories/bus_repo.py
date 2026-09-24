"""Data access for buses — plain SQL on sqlite3, no ORM."""
import sqlite3
from typing import Optional

from app.models.bus import COLUMNS, TABLE, Bus
from app.utils.time_utils import now_iso

SORTABLE = set(COLUMNS)


def _to_db_bool(value):
    return None if value is None else int(bool(value))


def create(conn: sqlite3.Connection, data: dict) -> Bus:
    ts = now_iso()
    cur = conn.execute(
        "INSERT INTO buses ("
        "registration_no, depot_id, capacity, bus_type, manufacture_year, is_operational, created_at, updated_at"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            data.get("registration_no"),
            data.get("depot_id"),
            data.get("capacity", 60),
            data.get("bus_type", 'ordinary'),
            data.get("manufacture_year"),
            _to_db_bool(data.get("is_operational", True)),
            ts,
            ts,
        ),
    )
    return get(conn, cur.lastrowid)


def get(conn: sqlite3.Connection, item_id: int) -> Optional[Bus]:
    row = conn.execute("SELECT * FROM buses WHERE id = ?", (item_id,)).fetchone()
    return Bus.from_row(row) if row else None


def get_by_registration_no(conn: sqlite3.Connection, value) -> Optional[Bus]:
    row = conn.execute("SELECT * FROM buses WHERE registration_no = ?", (value,)).fetchone()
    return Bus.from_row(row) if row else None


def exists(conn: sqlite3.Connection, item_id: int) -> bool:
    return conn.execute("SELECT 1 FROM buses WHERE id = ?", (item_id,)).fetchone() is not None


def _where(filters: Optional[dict]) -> tuple[str, list]:
    filters = filters or {}
    clauses: list[str] = []
    params: list = []
    if filters.get("registration_no") is not None:
        clauses.append("registration_no = ?")
        params.append(filters["registration_no"])
    if filters.get("depot_id") is not None:
        clauses.append("depot_id = ?")
        params.append(filters["depot_id"])
    if filters.get("min_capacity") is not None:
        clauses.append("capacity >= ?")
        params.append(filters["min_capacity"])
    if filters.get("max_capacity") is not None:
        clauses.append("capacity <= ?")
        params.append(filters["max_capacity"])
    if filters.get("bus_type") is not None:
        clauses.append("bus_type = ?")
        params.append(filters["bus_type"])
    if filters.get("min_manufacture_year") is not None:
        clauses.append("manufacture_year >= ?")
        params.append(filters["min_manufacture_year"])
    if filters.get("max_manufacture_year") is not None:
        clauses.append("manufacture_year <= ?")
        params.append(filters["max_manufacture_year"])
    if filters.get("is_operational") is not None:
        clauses.append("is_operational = ?")
        params.append(_to_db_bool(filters["is_operational"]))
    sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return sql, params


def list_(conn: sqlite3.Connection, filters: Optional[dict] = None, limit: int = 50, offset: int = 0,
          order_by: str = "id", descending: bool = False) -> list[Bus]:
    if order_by not in SORTABLE:
        order_by = "id"
    where, params = _where(filters)
    direction = "DESC" if descending else "ASC"
    sql = f"SELECT * FROM buses{where} ORDER BY {order_by} {direction} LIMIT ? OFFSET ?"
    rows = conn.execute(sql, [*params, limit, offset]).fetchall()
    return [Bus.from_row(r) for r in rows]


def count(conn: sqlite3.Connection, filters: Optional[dict] = None) -> int:
    where, params = _where(filters)
    return conn.execute(f"SELECT COUNT(*) FROM buses{where}", params).fetchone()[0]


def update(conn: sqlite3.Connection, item_id: int, changes: dict) -> Optional[Bus]:
    allowed = {}
    if changes.get("registration_no") is not None:
        allowed["registration_no"] = changes["registration_no"]
    if changes.get("depot_id") is not None:
        allowed["depot_id"] = changes["depot_id"]
    if changes.get("capacity") is not None:
        allowed["capacity"] = changes["capacity"]
    if changes.get("bus_type") is not None:
        allowed["bus_type"] = changes["bus_type"]
    if changes.get("manufacture_year") is not None:
        allowed["manufacture_year"] = changes["manufacture_year"]
    if changes.get("is_operational") is not None:
        allowed["is_operational"] = _to_db_bool(changes["is_operational"])
    if not allowed:
        return get(conn, item_id)
    assignments = ", ".join(f"{column} = ?" for column in allowed)
    conn.execute(
        f"UPDATE buses SET {assignments}, updated_at = ? WHERE id = ?",
        [*allowed.values(), now_iso(), item_id],
    )
    return get(conn, item_id)


def delete(conn: sqlite3.Connection, item_id: int) -> bool:
    cur = conn.execute("DELETE FROM buses WHERE id = ?", (item_id,))
    return cur.rowcount > 0


def bulk_create(conn: sqlite3.Connection, items: list[dict]) -> list[Bus]:
    return [create(conn, item) for item in items]
