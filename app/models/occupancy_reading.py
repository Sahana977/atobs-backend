"""Occupancy Readings data model.

Observed passenger load on a trip at a stop (ground truth for training).

Table: occupancy_readings
"""
from dataclasses import asdict, dataclass
from typing import Optional

TABLE = "occupancy_readings"

SOURCE_CHOICES = ('apc', 'ticketing', 'manual', 'simulated',)

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS occupancy_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id INTEGER NOT NULL REFERENCES trips(id),
    stop_id INTEGER NOT NULL REFERENCES stops(id),
    recorded_at TEXT NOT NULL,
    passengers_on_board INTEGER NOT NULL,
    occupancy_pct REAL NOT NULL,
    delay_min REAL DEFAULT 0.0,
    source TEXT DEFAULT 'apc',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_occupancy_readings_trip_id ON occupancy_readings (trip_id);",
    "CREATE INDEX IF NOT EXISTS idx_occupancy_readings_stop_id ON occupancy_readings (stop_id);",
    "CREATE INDEX IF NOT EXISTS idx_occupancy_readings_recorded_at ON occupancy_readings (recorded_at);",
    "CREATE INDEX IF NOT EXISTS idx_occupancy_readings_source ON occupancy_readings (source);",
]

FIELDS = [
    "trip_id",
    "stop_id",
    "recorded_at",
    "passengers_on_board",
    "occupancy_pct",
    "delay_min",
    "source",
]
COLUMNS = ["id", *FIELDS, "created_at", "updated_at"]
BOOL_FIELDS = []


def _as_bool(value):
    return None if value is None else bool(value)


@dataclass
class OccupancyReading:
    id: int
    trip_id: int
    stop_id: int
    recorded_at: str
    passengers_on_board: int
    occupancy_pct: float
    delay_min: float
    source: str
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row) -> "OccupancyReading":
        return cls(
            id=row["id"],
            trip_id=row["trip_id"],
            stop_id=row["stop_id"],
            recorded_at=row["recorded_at"],
            passengers_on_board=row["passengers_on_board"],
            occupancy_pct=row["occupancy_pct"],
            delay_min=row["delay_min"],
            source=row["source"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def to_dict(self) -> dict:
        return asdict(self)
