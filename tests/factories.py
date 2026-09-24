"""Test data builders — each make_x() creates a valid record (and its parents)."""
import itertools

from app.services import depot_service
from app.services import stop_service
from app.services import route_service
from app.services import route_stop_service
from app.services import bus_service
from app.services import trip_service
from app.services import traffic_reading_service
from app.services import occupancy_reading_service
from app.services import alert_service
from app.services import app_user_service
from app.services import feedback_service

_counter = itertools.count(1)


def valid_depot_data(**overrides) -> dict:
    n = next(_counter)
    data = {
        "depot_code": f"DEP{n:04d}",
        "name": f"Depot {n}",
        "area": "Marathahalli",
        "capacity": 120,
        "latitude": 12.9569,
        "longitude": 77.7011,
        "is_active": True,
    }
    data.update(overrides)
    return data


def make_depot(**overrides):
    return depot_service.create(valid_depot_data(**overrides))


def valid_stop_data(**overrides) -> dict:
    n = next(_counter)
    data = {
        "stop_code": f"STP{n:04d}",
        "name": f"Stop {n}",
        "area": "Whitefield",
        "latitude": 12.9698,
        "longitude": 77.7500,
        "zone": "core",
        "has_shelter": True,
        "is_accessible": True,
    }
    data.update(overrides)
    return data


def make_stop(**overrides):
    return stop_service.create(valid_stop_data(**overrides))


def valid_route_data(**overrides) -> dict:
    n = next(_counter)
    data = {
        "route_number": f"R{n}",
        "name": f"Route {n}",
        "origin_stop_id": make_stop().id,
        "destination_stop_id": make_stop().id,
        "distance_km": 12.5,
        "service_type": "ordinary",
        "avg_headway_min": 15,
        "is_active": True,
    }
    data.update(overrides)
    return data


def make_route(**overrides):
    return route_service.create(valid_route_data(**overrides))


def valid_route_stop_data(**overrides) -> dict:
    n = next(_counter)
    data = {
        "route_id": make_route().id,
        "stop_id": make_stop().id,
        "sequence": n % 200 + 1,
        "minutes_from_start": 12.0,
    }
    data.update(overrides)
    return data


def make_route_stop(**overrides):
    return route_stop_service.create(valid_route_stop_data(**overrides))


def valid_bus_data(**overrides) -> dict:
    n = next(_counter)
    data = {
        "registration_no": f"KA01F{n:04d}",
        "depot_id": make_depot().id,
        "capacity": 60,
        "bus_type": "electric",
        "manufacture_year": 2021,
        "is_operational": True,
    }
    data.update(overrides)
    return data


def make_bus(**overrides):
    return bus_service.create(valid_bus_data(**overrides))


def valid_trip_data(**overrides) -> dict:
    n = next(_counter)
    data = {
        "trip_code": f"T{n:05d}",
        "route_id": make_route().id,
        "bus_id": make_bus().id,
        "scheduled_start": "2026-10-01T08:00:00",
        "scheduled_end": "2026-10-01T09:10:00",
        "status": "scheduled",
    }
    data.update(overrides)
    return data


def make_trip(**overrides):
    return trip_service.create(valid_trip_data(**overrides))


def valid_traffic_reading_data(**overrides) -> dict:
    n = next(_counter)
    data = {
        "stop_id": make_stop().id,
        "recorded_at": "2026-10-01T08:30:00",
        "traffic_level": "high",
        "vehicle_density": 70.0,
        "avg_speed": 27.0,
        "road_occupancy": 0.56,
        "traffic_flow": 190.0,
        "source": "sensor",
    }
    data.update(overrides)
    return data


def make_traffic_reading(**overrides):
    return traffic_reading_service.create(valid_traffic_reading_data(**overrides))


def valid_occupancy_reading_data(**overrides) -> dict:
    n = next(_counter)
    data = {
        "trip_id": make_trip().id,
        "stop_id": make_stop().id,
        "recorded_at": "2026-10-01T08:35:00",
        "passengers_on_board": 48,
        "occupancy_pct": 80.0,
        "delay_min": 3.5,
        "source": "apc",
    }
    data.update(overrides)
    return data


def make_occupancy_reading(**overrides):
    return occupancy_reading_service.create(valid_occupancy_reading_data(**overrides))


def valid_alert_data(**overrides) -> dict:
    n = next(_counter)
    data = {
        "title": f"Road closure {n}",
        "message": "Diversion via Outer Ring Road",
        "severity": "warning",
        "stop_id": make_stop().id,
        "route_id": make_route().id,
        "starts_at": "2026-10-01T08:00:00",
        "ends_at": "2026-10-02T08:00:00",
        "is_active": True,
    }
    data.update(overrides)
    return data


def make_alert(**overrides):
    return alert_service.create(valid_alert_data(**overrides))


def valid_app_user_data(**overrides) -> dict:
    n = next(_counter)
    data = {
        "email": f"user{n}@example.com",
        "full_name": f"User {n}",
        "role": "commuter",
        "home_stop_id": make_stop().id,
        "is_active": True,
    }
    data.update(overrides)
    return data


def make_app_user(**overrides):
    return app_user_service.create(valid_app_user_data(**overrides))


def valid_feedback_data(**overrides) -> dict:
    n = next(_counter)
    data = {
        "user_id": make_app_user().id,
        "trip_id": make_trip().id,
        "rating": 4,
        "comfort_rating": 3,
        "category": "crowding",
        "comment": "Bus was packed at 9am",
    }
    data.update(overrides)
    return data


def make_feedback(**overrides):
    return feedback_service.create(valid_feedback_data(**overrides))
