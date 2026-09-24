"""Traffic Readings data model.

Traffic sensor readings near a stop.

Table: traffic_readings
"""
from dataclasses import asdict, dataclass
from typing import Optional

TABLE = "traffic_readings"

TRAFFIC_LEVEL_CHOICES = ('low', 'medium', 'high', 'severe',)
SOURCE_CHOICES = ('sensor', 'manual', 'simulated',)

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS traffic_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stop_id INTEGER NOT NULL REFERENCES stops(id),
    recorded_at TEXT NOT NULL,
    traffic_level TEXT NOT NULL,
    vehicle_density REAL,
    avg_speed REAL,
    road_occupancy REAL,
    traffic_flow REAL,
    source TEXT DEFAULT 'sensor',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_traffic_readings_stop_id ON traffic_readings (stop_id);",
    "CREATE INDEX IF NOT EXISTS idx_traffic_readings_recorded_at ON traffic_readings (recorded_at);",
    "CREATE INDEX IF NOT EXISTS idx_traffic_readings_traffic_level ON traffic_readings (traffic_level);",
    "CREATE INDEX IF NOT EXISTS idx_traffic_readings_source ON traffic_readings (source);",
]

FIELDS = [
    "stop_id",
    "recorded_at",
    "traffic_level",
    "vehicle_density",
    "avg_speed",
    "road_occupancy",
    "traffic_flow",
    "source",
]
COLUMNS = ["id", *FIELDS, "created_at", "updated_at"]
BOOL_FIELDS = []


def _as_bool(value):
    return None if value is None else bool(value)


@dataclass
class TrafficReading:
    id: int
    stop_id: int
    recorded_at: str
    traffic_level: str
    vehicle_density: Optional[float]
    avg_speed: Optional[float]
    road_occupancy: Optional[float]
    traffic_flow: Optional[float]
    source: str
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row) -> "TrafficReading":
        return cls(
            id=row["id"],
            stop_id=row["stop_id"],
            recorded_at=row["recorded_at"],
            traffic_level=row["traffic_level"],
            vehicle_density=row["vehicle_density"],
            avg_speed=row["avg_speed"],
            road_occupancy=row["road_occupancy"],
            traffic_flow=row["traffic_flow"],
            source=row["source"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def to_dict(self) -> dict:
        return asdict(self)
