"""Glue between the stored network (trips, route stops) and the ML model."""
from app import database
from app.errors import NotFoundError, ValidationError
from app.ml import predictor
from app.repositories import route_repo, trip_repo
from app.utils.time_utils import add_minutes, parse_iso


def predict_for_trip(trip_id: int, traffic_level: str = "medium", delay_min: float = 0.0) -> dict:
    """Predicted occupancy at every stop of a stored trip, in route order."""
    with database.session() as conn:
        trip = trip_repo.get(conn, trip_id)
        if trip is None:
            raise NotFoundError(f"trip {trip_id} not found")
        route = route_repo.get(conn, trip.route_id)
        stops = conn.execute("""
            SELECT rs.sequence, rs.minutes_from_start, s.id AS stop_id, s.stop_code, s.name
            FROM route_stops rs JOIN stops s ON s.id = rs.stop_id
            WHERE rs.route_id = ?
            ORDER BY rs.sequence
        """, (trip.route_id,)).fetchall()
    if not stops:
        raise ValidationError({"route_id": "this trip's route has no stops yet (add them via /route-stops)"})

    rows, arrivals = [], []
    for s in stops:
        arrival = add_minutes(trip.scheduled_start, s["minutes_from_start"] + delay_min)
        arrivals.append(arrival)
        rows.append(predictor.build_row(trip.trip_code, s["stop_code"], parse_iso(arrival),
                                        traffic_level, delay_min))
    preds = predictor.predict_rows(rows)

    stop_results = []
    for s, arrival, occ in zip(stops, arrivals, preds):
        stop_results.append({
            "sequence": s["sequence"], "stop_id": s["stop_id"], "stop_code": s["stop_code"],
            "name": s["name"], "expected_arrival": arrival,
            "predicted_occupancy_pct": occ, "comfort": predictor.comfort_label(occ),
        })
    peak = max(stop_results, key=lambda r: r["predicted_occupancy_pct"])
    return {
        "trip_id": trip.id, "trip_code": trip.trip_code,
        "route_number": route.route_number if route else None,
        "traffic_level": traffic_level, "delay_min": delay_min,
        "model": predictor.load()["name"],
        "most_crowded_stop": peak["name"],
        "max_occupancy_pct": peak["predicted_occupancy_pct"],
        "stops": stop_results,
    }
