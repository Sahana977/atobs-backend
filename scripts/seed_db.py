"""
Fill the database with a realistic sample network around Marathahalli so every
endpoint has something to show.

Run:  python -m scripts.seed_db            (wipes and re-seeds data/atobs.db)
"""
import math
import random

from app import database
from app.routing import graph
from app.services import (alert_service, auth_service, bus_service, depot_service,
                          feedback_service, occupancy_reading_service, route_service,
                          route_stop_service, stop_service, traffic_reading_service, trip_service)

SEED_DATE = "2026-10-01"
BASE_LAT, BASE_LON = 12.9569, 77.7011  # Marathahalli
TRAFFIC_BY_HOUR = {h: ("severe" if h in (9, 18) else "high" if h in (8, 10, 17, 19)
                       else "medium" if 7 <= h <= 21 else "low") for h in range(24)}
LEVEL_INDEX = {"low": 0, "medium": 1, "high": 2, "severe": 3}

ROUTE_PLANS = [
    ("500D", "Marathahalli Bridge", "Whitefield", "ordinary"),
    ("500K", "KR Puram", "Bellandur", "ordinary"),
    ("335E", "Kadugodi", "HAL", "ordinary"),
    ("V-500D", "Hope Farm", "Sarjapur Road Jn", "vajra"),
    ("KIA-5", "ITPL", "Marathahalli Bridge", "vayu_vajra"),
    ("MF-12", "Mahadevapura", "Kundalahalli Gate", "metro_feeder"),
    ("501A", "Varthur Kodi", "Tin Factory", "ordinary"),
    ("502B", "Panathur", "Hoodi", "ordinary"),
]


def seed_depots() -> list:
    rows = [
        {"depot_code": "DEP-WFD", "name": "Whitefield Depot", "area": "Whitefield", "capacity": 180,
         "latitude": 12.9698, "longitude": 77.7500},
        {"depot_code": "DEP-MTH", "name": "Marathahalli Depot", "area": "Marathahalli", "capacity": 150,
         "latitude": 12.9569, "longitude": 77.7011},
        {"depot_code": "DEP-KRP", "name": "KR Puram Depot", "area": "KR Puram", "capacity": 120,
         "latitude": 13.0077, "longitude": 77.6960},
    ]
    return depot_service.bulk_create(rows)


def seed_stops() -> dict:
    """One stop per graph node, laid out on a rough circle around Marathahalli."""
    rows = []
    for i, name in enumerate(graph.STOPS):
        angle = 2 * math.pi * i / len(graph.STOPS)
        rows.append({
            "stop_code": graph.STOP_IDS[name],
            "name": name,
            "area": name.split()[0],
            "latitude": round(BASE_LAT + 0.04 * math.sin(angle), 5),
            "longitude": round(BASE_LON + 0.05 * math.cos(angle), 5),
            "zone": "core" if i % 3 else "suburban",
            "has_shelter": i % 2 == 0,
            "is_accessible": i % 5 != 0,
        })
    return {s.name: s for s in stop_service.bulk_create(rows)}


def seed_routes(stops: dict) -> list:
    """Each route follows the fastest path through the road graph."""
    created = []
    edge_minutes = {}
    for e in graph.EDGES:
        edge_minutes[(e.a, e.b)] = edge_minutes[(e.b, e.a)] = (e.base_minutes, e.distance_km)

    for number, origin, destination, service_type in ROUTE_PLANS:
        path = graph.dijkstra(graph.resolve_stop(origin), graph.resolve_stop(destination),
                              {k: v[0] for k, v in edge_minutes.items()})
        distance = sum(edge_minutes[(a, b)][1] for a, b in zip(path, path[1:]))
        route = route_service.create({
            "route_number": number,
            "name": f"{origin} - {destination}",
            "origin_stop_id": stops[origin].id,
            "destination_stop_id": stops[destination].id,
            "distance_km": round(max(distance, 0.1), 2),
            "service_type": service_type,
            "avg_headway_min": 20 if service_type == "ordinary" else 40,
        })
        minutes = 0.0
        route_stops = []
        for seq, node in enumerate(path, start=1):
            if seq > 1:
                minutes += edge_minutes[(path[seq - 2], node)][0]
            route_stops.append({"route_id": route.id, "stop_id": stops[graph.STOPS[node]].id,
                                "sequence": seq, "minutes_from_start": round(minutes, 1)})
        route_stop_service.bulk_create(route_stops)
        created.append((route, route_stops))
    return created


def seed_fleet(depots: list, rng: random.Random) -> list:
    buses = []
    for i in range(1, 41):
        depot = depots[i % len(depots)]
        buses.append({
            "registration_no": f"KA01F{i:04d}",
            "depot_id": depot.id,
            "capacity": rng.choice([45, 60, 60, 72]),
            "bus_type": rng.choice(["ordinary", "ordinary", "ac", "electric", "midi"]),
            "manufacture_year": rng.randint(2012, 2025),
            "is_operational": rng.random() > 0.08,
        })
    return bus_service.bulk_create(buses)


def seed_trips(routes: list, buses: list) -> list:
    rows, n = [], 0
    for route, route_stops in routes:
        duration = route_stops[-1]["minutes_from_start"] + 5
        for hour in range(6, 23):
            n += 1
            start_min = hour * 60
            end_min = start_min + int(duration)
            rows.append({
                "trip_code": f"T{n:05d}",
                "route_id": route.id,
                "bus_id": buses[n % len(buses)].id,
                "scheduled_start": f"{SEED_DATE}T{start_min // 60:02d}:{start_min % 60:02d}:00",
                "scheduled_end": f"{SEED_DATE}T{min(end_min // 60, 23):02d}:{end_min % 60:02d}:00",
                "status": "completed" if hour < 12 else "scheduled",
            })
    return trip_service.bulk_create(rows)


def seed_traffic(stops: dict, rng: random.Random) -> None:
    rows = []
    for stop in stops.values():
        for hour in range(6, 23):
            level = TRAFFIC_BY_HOUR[hour]
            idx = LEVEL_INDEX[level]
            rows.append({
                "stop_id": stop.id,
                "recorded_at": f"{SEED_DATE}T{hour:02d}:15:00",
                "traffic_level": level,
                "vehicle_density": round(20 + idx * 25 + rng.gauss(0, 6), 1),
                "avg_speed": round(max(4.0, 45 - idx * 9 + rng.gauss(0, 3)), 1),
                "road_occupancy": round(min(1.0, max(0.05, 0.2 + idx * 0.18 + rng.gauss(0, 0.04))), 3),
                "traffic_flow": round(max(10.0, 150 + idx * 15 + rng.gauss(0, 20)), 1),
                "source": "simulated",
            })
    traffic_reading_service.bulk_create(rows)


def seed_occupancy(trips: list, routes: list, rng: random.Random) -> None:
    stops_by_route = {route.id: rs for route, rs in routes}
    rows = []
    for trip in trips:
        hour = int(trip.scheduled_start[11:13])
        idx = LEVEL_INDEX[TRAFFIC_BY_HOUR[hour]]
        peak = 1 if hour in (8, 9, 10, 17, 18, 19) else 0
        route_stops = stops_by_route[trip.route_id]
        for rs in route_stops:
            middle = 1 - abs(rs["sequence"] - len(route_stops) / 2) / len(route_stops)
            delay = max(0.0, idx * 2.5 + rng.gauss(0, 1.5))
            occ = max(0.0, min(150.0, 30 + 25 * peak + 6 * idx + 20 * middle + rng.gauss(0, 7)))
            minute = min(59, int(rs["minutes_from_start"]) % 60)
            rows.append({
                "trip_id": trip.id,
                "stop_id": rs["stop_id"],
                "recorded_at": f"{SEED_DATE}T{hour:02d}:{minute:02d}:00",
                "passengers_on_board": int(occ * 0.6),
                "occupancy_pct": round(occ, 1),
                "delay_min": round(delay, 1),
                "source": "simulated",
            })
    occupancy_reading_service.bulk_create(rows)


def seed_people_and_feedback(stops: dict, trips: list, rng: random.Random) -> None:
    users = [
        auth_service.register("admin@atobs.dev", "ATOBS Admin", "admin12345", role="admin"),
        auth_service.register("operator@atobs.dev", "Depot Operator", "operator12345", role="operator"),
    ]
    for i in range(1, 6):
        users.append(auth_service.register(f"commuter{i}@atobs.dev", f"Commuter {i}", f"commuter{i}pass"))

    comments = {
        "crowding": ["Standing room only near Marathahalli", "Too crowded at 9am"],
        "delay": ["Bus was 15 minutes late", "Stuck at the ORR junction"],
        "cleanliness": ["Seats were dirty"],
        "staff": ["Conductor was very helpful"],
        "other": ["Would love live occupancy on the app"],
    }
    rows = []
    for _ in range(40):
        category = rng.choice(list(comments))
        rows.append({
            "user_id": rng.choice(users[2:]).id,
            "trip_id": rng.choice(trips).id,
            "rating": rng.randint(1, 5),
            "comfort_rating": rng.randint(1, 5) if category != "crowding" else rng.randint(1, 2),
            "category": category,
            "comment": rng.choice(comments[category]),
        })
    feedback_service.bulk_create(rows)

    alert_service.bulk_create([
        {"title": "Metro work near KR Puram", "message": "Expect 10-15 min delays on 500K.",
         "severity": "warning", "stop_id": stops["KR Puram"].id,
         "starts_at": f"{SEED_DATE}T06:00:00", "ends_at": "2026-12-31T23:00:00"},
        {"title": "Waterlogging at Bellandur", "message": "Buses diverted via Sarjapur Road.",
         "severity": "critical", "stop_id": stops["Bellandur"].id,
         "starts_at": f"{SEED_DATE}T08:00:00", "ends_at": f"{SEED_DATE}T20:00:00"},
        {"title": "New electric buses on V-500D", "message": "More AC capacity during peak hours.",
         "severity": "info", "starts_at": f"{SEED_DATE}T06:00:00"},
    ])


def main(seed: int = 42) -> None:
    rng = random.Random(seed)
    database.reset_db()
    depots = seed_depots()
    stops = seed_stops()
    routes = seed_routes(stops)
    buses = seed_fleet(depots, rng)
    trips = seed_trips(routes, buses)
    seed_traffic(stops, rng)
    seed_occupancy(trips, routes, rng)
    seed_people_and_feedback(stops, trips, rng)
    print(f"Seeded: {len(depots)} depots, {len(stops)} stops, {len(routes)} routes, "
          f"{len(buses)} buses, {len(trips)} trips")
    print("Logins: admin@atobs.dev / admin12345, commuter1@atobs.dev / commuter1pass")


if __name__ == "__main__":
    main()
