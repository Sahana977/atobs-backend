"""Routes data model.

Bus routes (e.g. 500D) running between two stops.

Table: routes
"""
from dataclasses import asdict, dataclass
from typing import Optional

TABLE = "routes"

SERVICE_TYPE_CHOICES = ('ordinary', 'vajra', 'vayu_vajra', 'metro_feeder',)

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_number TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    origin_stop_id INTEGER NOT NULL REFERENCES stops(id),
    destination_stop_id INTEGER NOT NULL REFERENCES stops(id),
    distance_km REAL NOT NULL,
    service_type TEXT DEFAULT 'ordinary',
    avg_headway_min INTEGER DEFAULT 15,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_routes_origin_stop_id ON routes (origin_stop_id);",
    "CREATE INDEX IF NOT EXISTS idx_routes_destination_stop_id ON routes (destination_stop_id);",
    "CREATE INDEX IF NOT EXISTS idx_routes_service_type ON routes (service_type);",
]

FIELDS = [
    "route_number",
    "name",
    "origin_stop_id",
    "destination_stop_id",
    "distance_km",
    "service_type",
    "avg_headway_min",
    "is_active",
]
COLUMNS = ["id", *FIELDS, "created_at", "updated_at"]
BOOL_FIELDS = ["is_active"]


def _as_bool(value):
    return None if value is None else bool(value)


@dataclass
class Route:
    id: int
    route_number: str
    name: str
    origin_stop_id: int
    destination_stop_id: int
    distance_km: float
    service_type: str
    avg_headway_min: int
    is_active: bool
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row) -> "Route":
        return cls(
            id=row["id"],
            route_number=row["route_number"],
            name=row["name"],
            origin_stop_id=row["origin_stop_id"],
            destination_stop_id=row["destination_stop_id"],
            distance_km=row["distance_km"],
            service_type=row["service_type"],
            avg_headway_min=row["avg_headway_min"],
            is_active=_as_bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def to_dict(self) -> dict:
        return asdict(self)
