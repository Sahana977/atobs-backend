"""Trips data model.

A scheduled run of a bus on a route.

Table: trips
"""
from dataclasses import asdict, dataclass
from typing import Optional

TABLE = "trips"

STATUS_CHOICES = ('scheduled', 'running', 'completed', 'cancelled',)

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_code TEXT NOT NULL UNIQUE,
    route_id INTEGER NOT NULL REFERENCES routes(id),
    bus_id INTEGER NOT NULL REFERENCES buses(id),
    scheduled_start TEXT NOT NULL,
    scheduled_end TEXT,
    status TEXT DEFAULT 'scheduled',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_trips_route_id ON trips (route_id);",
    "CREATE INDEX IF NOT EXISTS idx_trips_bus_id ON trips (bus_id);",
    "CREATE INDEX IF NOT EXISTS idx_trips_scheduled_start ON trips (scheduled_start);",
    "CREATE INDEX IF NOT EXISTS idx_trips_scheduled_end ON trips (scheduled_end);",
    "CREATE INDEX IF NOT EXISTS idx_trips_status ON trips (status);",
]

FIELDS = [
    "trip_code",
    "route_id",
    "bus_id",
    "scheduled_start",
    "scheduled_end",
    "status",
]
COLUMNS = ["id", *FIELDS, "created_at", "updated_at"]
BOOL_FIELDS = []


def _as_bool(value):
    return None if value is None else bool(value)


@dataclass
class Trip:
    id: int
    trip_code: str
    route_id: int
    bus_id: int
    scheduled_start: str
    scheduled_end: Optional[str]
    status: str
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row) -> "Trip":
        return cls(
            id=row["id"],
            trip_code=row["trip_code"],
            route_id=row["route_id"],
            bus_id=row["bus_id"],
            scheduled_start=row["scheduled_start"],
            scheduled_end=row["scheduled_end"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def to_dict(self) -> dict:
        return asdict(self)
