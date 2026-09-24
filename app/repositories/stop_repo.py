"""Data access for stops — plain SQL on sqlite3, no ORM."""
import sqlite3
from typing import Optional

from app.models.stop import COLUMNS, TABLE, Stop
from app.utils.time_utils import now_iso

SORTABLE = set(COLUMNS)


def _to_db_bool(value):
    return None if value is None else int(bool(value))


def create(conn: sqlite3.Connection, data: dict) -> Stop:
    ts = now_iso()
    cur = conn.execute(
        "INSERT INTO stops ("
        "stop_code, name, area, latitude, longitude, zone, has_shelter, is_accessible, created_at, updated_at"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            data.get("stop_code"),
            data.get("name"),
            data.get("area"),
            data.get("latitude"),
            data.get("longitude"),
            data.get("zone", 'core'),
            _to_db_bool(data.get("has_shelter", False)),
            _to_db_bool(data.get("is_accessible", True)),
            ts,
            ts,
        ),
    )
    return get(conn, cur.lastrowid)


def get(conn: sqlite3.Connection, item_id: int) -> Optional[Stop]:
    row = conn.execute("SELECT * FROM stops WHERE id = ?", (item_id,)).fetchone()
    return Stop.from_row(row) if row else None


def get_by_stop_code(conn: sqlite3.Connection, value) -> Optional[Stop]:
    row = conn.execute("SELECT * FROM stops WHERE stop_code = ?", (value,)).fetchone()
    return Stop.from_row(row) if row else None


def exists(conn: sqlite3.Connection, item_id: int) -> bool:
    return conn.execute("SELECT 1 FROM stops WHERE id = ?", (item_id,)).fetchone() is not None


def _where(filters: Optional[dict]) -> tuple[str, list]:
    filters = filters or {}
    clauses: list[str] = []
    params: list = []
    if filters.get("stop_code") is not None:
        clauses.append("stop_code = ?")
        params.append(filters["stop_code"])
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
    if filters.get("zone") is not None:
        clauses.append("zone = ?")
        params.append(filters["zone"])
    if filters.get("has_shelter") is not None:
        clauses.append("has_shelter = ?")
        params.append(_to_db_bool(filters["has_shelter"]))
    if filters.get("is_accessible") is not None:
        clauses.append("is_accessible = ?")
        params.append(_to_db_bool(filters["is_accessible"]))
    if filters.get("q"):
        clauses.append("(name LIKE ? OR area LIKE ?)")
        like = f"%{filters['q']}%"
        params.extend([like] * 2)
    sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return sql, params


def list_(conn: sqlite3.Connection, filters: Optional[dict] = None, limit: int = 50, offset: int = 0,
          order_by: str = "id", descending: bool = False) -> list[Stop]:
    if order_by not in SORTABLE:
        order_by = "id"
    where, params = _where(filters)
    direction = "DESC" if descending else "ASC"
    sql = f"SELECT * FROM stops{where} ORDER BY {order_by} {direction} LIMIT ? OFFSET ?"
    rows = conn.execute(sql, [*params, limit, offset]).fetchall()
    return [Stop.from_row(r) for r in rows]


def count(conn: sqlite3.Connection, filters: Optional[dict] = None) -> int:
    where, params = _where(filters)
    return conn.execute(f"SELECT COUNT(*) FROM stops{where}", params).fetchone()[0]


def update(conn: sqlite3.Connection, item_id: int, changes: dict) -> Optional[Stop]:
    allowed = {}
    if changes.get("stop_code") is not None:
        allowed["stop_code"] = changes["stop_code"]
    if changes.get("name") is not None:
        allowed["name"] = changes["name"]
    if changes.get("area") is not None:
        allowed["area"] = changes["area"]
    if changes.get("latitude") is not None:
        allowed["latitude"] = changes["latitude"]
    if changes.get("longitude") is not None:
        allowed["longitude"] = changes["longitude"]
    if changes.get("zone") is not None:
        allowed["zone"] = changes["zone"]
    if changes.get("has_shelter") is not None:
        allowed["has_shelter"] = _to_db_bool(changes["has_shelter"])
    if changes.get("is_accessible") is not None:
        allowed["is_accessible"] = _to_db_bool(changes["is_accessible"])
    if not allowed:
        return get(conn, item_id)
    assignments = ", ".join(f"{column} = ?" for column in allowed)
    conn.execute(
        f"UPDATE stops SET {assignments}, updated_at = ? WHERE id = ?",
        [*allowed.values(), now_iso(), item_id],
    )
    return get(conn, item_id)


def delete(conn: sqlite3.Connection, item_id: int) -> bool:
    cur = conn.execute("DELETE FROM stops WHERE id = ?", (item_id,))
    return cur.rowcount > 0


def bulk_create(conn: sqlite3.Connection, items: list[dict]) -> list[Stop]:
    return [create(conn, item) for item in items]
