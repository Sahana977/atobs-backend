"""Alerts data model.

Service disruptions such as accidents or road closures.

Table: alerts
"""
from dataclasses import asdict, dataclass
from typing import Optional

TABLE = "alerts"

SEVERITY_CHOICES = ('info', 'warning', 'critical',)

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    severity TEXT DEFAULT 'info',
    stop_id INTEGER REFERENCES stops(id),
    route_id INTEGER REFERENCES routes(id),
    starts_at TEXT NOT NULL,
    ends_at TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts (severity);",
    "CREATE INDEX IF NOT EXISTS idx_alerts_stop_id ON alerts (stop_id);",
    "CREATE INDEX IF NOT EXISTS idx_alerts_route_id ON alerts (route_id);",
    "CREATE INDEX IF NOT EXISTS idx_alerts_starts_at ON alerts (starts_at);",
    "CREATE INDEX IF NOT EXISTS idx_alerts_ends_at ON alerts (ends_at);",
]

FIELDS = [
    "title",
    "message",
    "severity",
    "stop_id",
    "route_id",
    "starts_at",
    "ends_at",
    "is_active",
]
COLUMNS = ["id", *FIELDS, "created_at", "updated_at"]
BOOL_FIELDS = ["is_active"]


def _as_bool(value):
    return None if value is None else bool(value)


@dataclass
class Alert:
    id: int
    title: str
    message: str
    severity: str
    stop_id: Optional[int]
    route_id: Optional[int]
    starts_at: str
    ends_at: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row) -> "Alert":
        return cls(
            id=row["id"],
            title=row["title"],
            message=row["message"],
            severity=row["severity"],
            stop_id=row["stop_id"],
            route_id=row["route_id"],
            starts_at=row["starts_at"],
            ends_at=row["ends_at"],
            is_active=_as_bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def to_dict(self) -> dict:
        return asdict(self)
