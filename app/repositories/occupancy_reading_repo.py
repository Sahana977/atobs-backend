"""Data access for occupancy readings — plain SQL on sqlite3, no ORM."""
import sqlite3
from typing import Optional

from app.models.occupancy_reading import COLUMNS, TABLE, OccupancyReading
from app.utils.time_utils import now_iso

SORTABLE = set(COLUMNS)


def _to_db_bool(value):
    return None if value is None else int(bool(value))


def create(conn: sqlite3.Connection, data: dict) -> OccupancyReading:
    ts = now_iso()
    cur = conn.execute(
        "INSERT INTO occupancy_readings ("
        "trip_id, stop_id, recorded_at, passengers_on_board, occupancy_pct, delay_min, source, created_at, updated_at"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            data.get("trip_id"),
            data.get("stop_id"),
            data.get("recorded_at"),
            data.get("passengers_on_board"),
            data.get("occupancy_pct"),
            data.get("delay_min", 0.0),
            data.get("source", 'apc'),
            ts,
            ts,
        ),
    )
    return get(conn, cur.lastrowid)


def get(conn: sqlite3.Connection, item_id: int) -> Optional[OccupancyReading]:
    row = conn.execute("SELECT * FROM occupancy_readings WHERE id = ?", (item_id,)).fetchone()
    return OccupancyReading.from_row(row) if row else None


def exists(conn: sqlite3.Connection, item_id: int) -> bool:
    return conn.execute("SELECT 1 FROM occupancy_readings WHERE id = ?", (item_id,)).fetchone() is not None


def _where(filters: Optional[dict]) -> tuple[str, list]:
    filters = filters or {}
    clauses: list[str] = []
    params: list = []
    if filters.get("trip_id") is not None:
        clauses.append("trip_id = ?")
        params.append(filters["trip_id"])
    if filters.get("stop_id") is not None:
        clauses.append("stop_id = ?")
        params.append(filters["stop_id"])
    if filters.get("recorded_at_from") is not None:
        clauses.append("recorded_at >= ?")
        params.append(filters["recorded_at_from"])
    if filters.get("recorded_at_to") is not None:
        clauses.append("recorded_at <= ?")
        params.append(filters["recorded_at_to"])
    if filters.get("min_passengers_on_board") is not None:
        clauses.append("passengers_on_board >= ?")
        params.append(filters["min_passengers_on_board"])
    if filters.get("max_passengers_on_board") is not None:
        clauses.append("passengers_on_board <= ?")
        params.append(filters["max_passengers_on_board"])
    if filters.get("min_occupancy_pct") is not None:
        clauses.append("occupancy_pct >= ?")
        params.append(filters["min_occupancy_pct"])
    if filters.get("max_occupancy_pct") is not None:
        clauses.append("occupancy_pct <= ?")
        params.append(filters["max_occupancy_pct"])
    if filters.get("min_delay_min") is not None:
        clauses.append("delay_min >= ?")
        params.append(filters["min_delay_min"])
    if filters.get("max_delay_min") is not None:
        clauses.append("delay_min <= ?")
        params.append(filters["max_delay_min"])
    if filters.get("source") is not None:
        clauses.append("source = ?")
        params.append(filters["source"])
    sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return sql, params


def list_(conn: sqlite3.Connection, filters: Optional[dict] = None, limit: int = 50, offset: int = 0,
          order_by: str = "id", descending: bool = False) -> list[OccupancyReading]:
    if order_by not in SORTABLE:
        order_by = "id"
    where, params = _where(filters)
    direction = "DESC" if descending else "ASC"
    sql = f"SELECT * FROM occupancy_readings{where} ORDER BY {order_by} {direction} LIMIT ? OFFSET ?"
    rows = conn.execute(sql, [*params, limit, offset]).fetchall()
    return [OccupancyReading.from_row(r) for r in rows]


def count(conn: sqlite3.Connection, filters: Optional[dict] = None) -> int:
    where, params = _where(filters)
    return conn.execute(f"SELECT COUNT(*) FROM occupancy_readings{where}", params).fetchone()[0]


def update(conn: sqlite3.Connection, item_id: int, changes: dict) -> Optional[OccupancyReading]:
    allowed = {}
    if changes.get("trip_id") is not None:
        allowed["trip_id"] = changes["trip_id"]
    if changes.get("stop_id") is not None:
        allowed["stop_id"] = changes["stop_id"]
    if changes.get("recorded_at") is not None:
        allowed["recorded_at"] = changes["recorded_at"]
    if changes.get("passengers_on_board") is not None:
        allowed["passengers_on_board"] = changes["passengers_on_board"]
    if changes.get("occupancy_pct") is not None:
        allowed["occupancy_pct"] = changes["occupancy_pct"]
    if changes.get("delay_min") is not None:
        allowed["delay_min"] = changes["delay_min"]
    if changes.get("source") is not None:
        allowed["source"] = changes["source"]
    if not allowed:
        return get(conn, item_id)
    assignments = ", ".join(f"{column} = ?" for column in allowed)
    conn.execute(
        f"UPDATE occupancy_readings SET {assignments}, updated_at = ? WHERE id = ?",
        [*allowed.values(), now_iso(), item_id],
    )
    return get(conn, item_id)


def delete(conn: sqlite3.Connection, item_id: int) -> bool:
    cur = conn.execute("DELETE FROM occupancy_readings WHERE id = ?", (item_id,))
    return cur.rowcount > 0


def bulk_create(conn: sqlite3.Connection, items: list[dict]) -> list[OccupancyReading]:
    return [create(conn, item) for item in items]
