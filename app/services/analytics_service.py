"""
Read-only reports built from the stored readings, trips and feedback.
Each function is one SQL query + a little tidying.
"""
from typing import Optional

from app import database
from app.ml.predictor import comfort_label, is_peak


def _rows(sql: str, params: tuple = ()) -> list[dict]:
    with database.session() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def occupancy_by_hour(route_id: Optional[int] = None) -> list[dict]:
    """Average observed occupancy for each hour of the day."""
    sql = """
        SELECT CAST(strftime('%H', o.recorded_at) AS INTEGER) AS hour,
               ROUND(AVG(o.occupancy_pct), 1) AS avg_occupancy_pct,
               ROUND(MAX(o.occupancy_pct), 1) AS max_occupancy_pct,
               COUNT(*) AS readings
        FROM occupancy_readings o
        JOIN trips t ON t.id = o.trip_id
    """
    params: tuple = ()
    if route_id is not None:
        sql += " WHERE t.route_id = ?"
        params = (route_id,)
    sql += " GROUP BY hour ORDER BY hour"
    rows = _rows(sql, params)
    for r in rows:
        r["comfort"] = comfort_label(r["avg_occupancy_pct"])
    return rows


def busiest_stops(limit: int = 10) -> list[dict]:
    rows = _rows("""
        SELECT s.id AS stop_id, s.stop_code, s.name,
               ROUND(AVG(o.occupancy_pct), 1) AS avg_occupancy_pct,
               COUNT(*) AS readings
        FROM occupancy_readings o
        JOIN stops s ON s.id = o.stop_id
        GROUP BY s.id
        ORDER BY avg_occupancy_pct DESC
        LIMIT ?
    """, (limit,))
    for r in rows:
        r["comfort"] = comfort_label(r["avg_occupancy_pct"])
    return rows


def route_performance() -> list[dict]:
    """Per route: average load, average and worst delay, number of trips observed."""
    return _rows("""
        SELECT r.id AS route_id, r.route_number, r.name,
               COUNT(DISTINCT t.id) AS trips_observed,
               ROUND(AVG(o.occupancy_pct), 1) AS avg_occupancy_pct,
               ROUND(AVG(o.delay_min), 1) AS avg_delay_min,
               ROUND(MAX(o.delay_min), 1) AS max_delay_min
        FROM routes r
        JOIN trips t ON t.route_id = r.id
        JOIN occupancy_readings o ON o.trip_id = t.id
        GROUP BY r.id
        ORDER BY avg_occupancy_pct DESC
    """)


def traffic_summary() -> dict:
    by_level = _rows("""
        SELECT traffic_level, COUNT(*) AS readings,
               ROUND(AVG(avg_speed), 1) AS avg_speed,
               ROUND(AVG(vehicle_density), 1) AS avg_density
        FROM traffic_readings
        GROUP BY traffic_level
        ORDER BY readings DESC
    """)
    worst = _rows("""
        SELECT s.id AS stop_id, s.name, ROUND(AVG(t.road_occupancy), 3) AS avg_road_occupancy
        FROM traffic_readings t JOIN stops s ON s.id = t.stop_id
        GROUP BY s.id ORDER BY avg_road_occupancy DESC LIMIT 5
    """)
    return {"by_level": by_level, "most_congested_stops": worst}


def fleet_summary() -> dict:
    with database.session() as conn:
        buses = conn.execute("""
            SELECT COUNT(*) AS total, COALESCE(SUM(is_operational), 0) AS operational FROM buses
        """).fetchone()
        by_type = conn.execute("SELECT bus_type, COUNT(*) AS n FROM buses GROUP BY bus_type").fetchall()
        trips = conn.execute("SELECT status, COUNT(*) AS n FROM trips GROUP BY status").fetchall()
    return {
        "buses_total": buses["total"],
        "buses_operational": buses["operational"],
        "buses_by_type": {r["bus_type"]: r["n"] for r in by_type},
        "trips_by_status": {r["status"]: r["n"] for r in trips},
    }


def feedback_summary() -> dict:
    with database.session() as conn:
        overall = conn.execute("""
            SELECT COUNT(*) AS total, ROUND(AVG(rating), 2) AS avg_rating,
                   ROUND(AVG(comfort_rating), 2) AS avg_comfort_rating
            FROM feedback
        """).fetchone()
        by_category = conn.execute(
            "SELECT category, COUNT(*) AS n FROM feedback GROUP BY category ORDER BY n DESC").fetchall()
    return {**dict(overall), "by_category": {r["category"]: r["n"] for r in by_category}}


def active_alerts() -> list[dict]:
    return _rows("""
        SELECT a.id, a.title, a.severity, a.starts_at, a.ends_at,
               s.name AS stop_name, r.route_number
        FROM alerts a
        LEFT JOIN stops s ON s.id = a.stop_id
        LEFT JOIN routes r ON r.id = a.route_id
        WHERE a.is_active = 1
        ORDER BY CASE a.severity WHEN 'critical' THEN 0 WHEN 'warning' THEN 1 ELSE 2 END, a.starts_at
    """)


def training_rows() -> list[dict]:
    """
    Joins observed occupancy with the nearest traffic reading at the same stop/hour,
    giving rows in the same shape as data/bmtc_raw.csv — so stored data can be used to retrain.
    """
    rows = _rows("""
        SELECT t.trip_code AS trip_id, s.stop_code AS stop_id,
               CAST(strftime('%H', o.recorded_at) AS INTEGER) * 60
                 + CAST(strftime('%M', o.recorded_at) AS INTEGER) AS minute_of_day,
               COALESCE(tr.traffic_level, 'medium') AS traffic_level,
               tr.vehicle_density, tr.avg_speed, tr.road_occupancy, tr.traffic_flow,
               o.delay_min, o.occupancy_pct
        FROM occupancy_readings o
        JOIN trips t ON t.id = o.trip_id
        JOIN stops s ON s.id = o.stop_id
        LEFT JOIN traffic_readings tr
               ON tr.stop_id = o.stop_id
              AND strftime('%Y-%m-%dT%H', tr.recorded_at) = strftime('%Y-%m-%dT%H', o.recorded_at)
        GROUP BY o.id
    """)
    for r in rows:
        r["is_peak_hour"] = is_peak(r["minute_of_day"])
    return rows


def dashboard() -> dict:
    return {
        "fleet": fleet_summary(),
        "busiest_stops": busiest_stops(5),
        "occupancy_by_hour": occupancy_by_hour(),
        "traffic": traffic_summary(),
        "feedback": feedback_summary(),
        "active_alerts": active_alerts(),
    }
