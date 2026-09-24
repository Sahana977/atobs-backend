"""Data access for traffic readings — plain SQL on sqlite3, no ORM."""
import sqlite3
from typing import Optional

from app.models.traffic_reading import COLUMNS, TABLE, TrafficReading
from app.utils.time_utils import now_iso

SORTABLE = set(COLUMNS)


def _to_db_bool(value):
    return None if value is None else int(bool(value))


def create(conn: sqlite3.Connection, data: dict) -> TrafficReading:
    ts = now_iso()
    cur = conn.execute(
        "INSERT INTO traffic_readings ("
        "stop_id, recorded_at, traffic_level, vehicle_density, avg_speed, road_occupancy, traffic_flow, source, created_at, updated_at"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            data.get("stop_id"),
            data.get("recorded_at"),
            data.get("traffic_level"),
            data.get("vehicle_density"),
            data.get("avg_speed"),
            data.get("road_occupancy"),
            data.get("traffic_flow"),
            data.get("source", 'sensor'),
            ts,
            ts,
        ),
    )
    return get(conn, cur.lastrowid)


def get(conn: sqlite3.Connection, item_id: int) -> Optional[TrafficReading]:
    row = conn.execute("SELECT * FROM traffic_readings WHERE id = ?", (item_id,)).fetchone()
    return TrafficReading.from_row(row) if row else None


def exists(conn: sqlite3.Connection, item_id: int) -> bool:
    return conn.execute("SELECT 1 FROM traffic_readings WHERE id = ?", (item_id,)).fetchone() is not None


def _where(filters: Optional[dict]) -> tuple[str, list]:
    filters = filters or {}
    clauses: list[str] = []
    params: list = []
    if filters.get("stop_id") is not None:
        clauses.append("stop_id = ?")
        params.append(filters["stop_id"])
    if filters.get("recorded_at_from") is not None:
        clauses.append("recorded_at >= ?")
        params.append(filters["recorded_at_from"])
    if filters.get("recorded_at_to") is not None:
        clauses.append("recorded_at <= ?")
        params.append(filters["recorded_at_to"])
    if filters.get("traffic_level") is not None:
        clauses.append("traffic_level = ?")
        params.append(filters["traffic_level"])
    if filters.get("min_vehicle_density") is not None:
        clauses.append("vehicle_density >= ?")
        params.append(filters["min_vehicle_density"])
    if filters.get("max_vehicle_density") is not None:
        clauses.append("vehicle_density <= ?")
        params.append(filters["max_vehicle_density"])
    if filters.get("min_avg_speed") is not None:
        clauses.append("avg_speed >= ?")
        params.append(filters["min_avg_speed"])
    if filters.get("max_avg_speed") is not None:
        clauses.append("avg_speed <= ?")
        params.append(filters["max_avg_speed"])
    if filters.get("min_road_occupancy") is not None:
        clauses.append("road_occupancy >= ?")
        params.append(filters["min_road_occupancy"])
    if filters.get("max_road_occupancy") is not None:
        clauses.append("road_occupancy <= ?")
        params.append(filters["max_road_occupancy"])
    if filters.get("min_traffic_flow") is not None:
        clauses.append("traffic_flow >= ?")
        params.append(filters["min_traffic_flow"])
    if filters.get("max_traffic_flow") is not None:
        clauses.append("traffic_flow <= ?")
        params.append(filters["max_traffic_flow"])
    if filters.get("source") is not None:
        clauses.append("source = ?")
        params.append(filters["source"])
    sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return sql, params


def list_(conn: sqlite3.Connection, filters: Optional[dict] = None, limit: int = 50, offset: int = 0,
          order_by: str = "id", descending: bool = False) -> list[TrafficReading]:
    if order_by not in SORTABLE:
        order_by = "id"
    where, params = _where(filters)
    direction = "DESC" if descending else "ASC"
    sql = f"SELECT * FROM traffic_readings{where} ORDER BY {order_by} {direction} LIMIT ? OFFSET ?"
    rows = conn.execute(sql, [*params, limit, offset]).fetchall()
    return [TrafficReading.from_row(r) for r in rows]


def count(conn: sqlite3.Connection, filters: Optional[dict] = None) -> int:
    where, params = _where(filters)
    return conn.execute(f"SELECT COUNT(*) FROM traffic_readings{where}", params).fetchone()[0]


def update(conn: sqlite3.Connection, item_id: int, changes: dict) -> Optional[TrafficReading]:
    allowed = {}
    if changes.get("stop_id") is not None:
        allowed["stop_id"] = changes["stop_id"]
    if changes.get("recorded_at") is not None:
        allowed["recorded_at"] = changes["recorded_at"]
    if changes.get("traffic_level") is not None:
        allowed["traffic_level"] = changes["traffic_level"]
    if changes.get("vehicle_density") is not None:
        allowed["vehicle_density"] = changes["vehicle_density"]
    if changes.get("avg_speed") is not None:
        allowed["avg_speed"] = changes["avg_speed"]
    if changes.get("road_occupancy") is not None:
        allowed["road_occupancy"] = changes["road_occupancy"]
    if changes.get("traffic_flow") is not None:
        allowed["traffic_flow"] = changes["traffic_flow"]
    if changes.get("source") is not None:
        allowed["source"] = changes["source"]
    if not allowed:
        return get(conn, item_id)
    assignments = ", ".join(f"{column} = ?" for column in allowed)
    conn.execute(
        f"UPDATE traffic_readings SET {assignments}, updated_at = ? WHERE id = ?",
        [*allowed.values(), now_iso(), item_id],
    )
    return get(conn, item_id)


def delete(conn: sqlite3.Connection, item_id: int) -> bool:
    cur = conn.execute("DELETE FROM traffic_readings WHERE id = ?", (item_id,))
    return cur.rowcount > 0


def bulk_create(conn: sqlite3.Connection, items: list[dict]) -> list[TrafficReading]:
    return [create(conn, item) for item in items]
