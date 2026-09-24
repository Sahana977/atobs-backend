"""Route Stops data model.

Ordered list of stops served by each route.

Table: route_stops
"""
from dataclasses import asdict, dataclass
from typing import Optional

TABLE = "route_stops"

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS route_stops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id INTEGER NOT NULL REFERENCES routes(id),
    stop_id INTEGER NOT NULL REFERENCES stops(id),
    sequence INTEGER NOT NULL,
    minutes_from_start REAL DEFAULT 0.0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_route_stops_route_id ON route_stops (route_id);",
    "CREATE INDEX IF NOT EXISTS idx_route_stops_stop_id ON route_stops (stop_id);",
]

FIELDS = [
    "route_id",
    "stop_id",
    "sequence",
    "minutes_from_start",
]
COLUMNS = ["id", *FIELDS, "created_at", "updated_at"]
BOOL_FIELDS = []


def _as_bool(value):
    return None if value is None else bool(value)


@dataclass
class RouteStop:
    id: int
    route_id: int
    stop_id: int
    sequence: int
    minutes_from_start: float
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row) -> "RouteStop":
        return cls(
            id=row["id"],
            route_id=row["route_id"],
            stop_id=row["stop_id"],
            sequence=row["sequence"],
            minutes_from_start=row["minutes_from_start"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def to_dict(self) -> dict:
        return asdict(self)
