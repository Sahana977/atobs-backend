"""Stops data model.

Bus stops — the nodes of the road graph.

Table: stops
"""
from dataclasses import asdict, dataclass
from typing import Optional

TABLE = "stops"

ZONE_CHOICES = ('core', 'suburban', 'outer',)

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS stops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stop_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    area TEXT,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    zone TEXT DEFAULT 'core',
    has_shelter INTEGER DEFAULT 0,
    is_accessible INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_stops_zone ON stops (zone);",
]

FIELDS = [
    "stop_code",
    "name",
    "area",
    "latitude",
    "longitude",
    "zone",
    "has_shelter",
    "is_accessible",
]
COLUMNS = ["id", *FIELDS, "created_at", "updated_at"]
BOOL_FIELDS = ["has_shelter", "is_accessible"]


def _as_bool(value):
    return None if value is None else bool(value)


@dataclass
class Stop:
    id: int
    stop_code: str
    name: str
    area: Optional[str]
    latitude: float
    longitude: float
    zone: str
    has_shelter: bool
    is_accessible: bool
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row) -> "Stop":
        return cls(
            id=row["id"],
            stop_code=row["stop_code"],
            name=row["name"],
            area=row["area"],
            latitude=row["latitude"],
            longitude=row["longitude"],
            zone=row["zone"],
            has_shelter=_as_bool(row["has_shelter"]),
            is_accessible=_as_bool(row["is_accessible"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def to_dict(self) -> dict:
        return asdict(self)
