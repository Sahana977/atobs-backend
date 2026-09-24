"""Depots data model.

BMTC bus depots that house the fleet.

Table: depots
"""
from dataclasses import asdict, dataclass
from typing import Optional

TABLE = "depots"

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS depots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    depot_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    area TEXT,
    capacity INTEGER DEFAULT 100,
    latitude REAL,
    longitude REAL,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

INDEX_SQL = [
]

FIELDS = [
    "depot_code",
    "name",
    "area",
    "capacity",
    "latitude",
    "longitude",
    "is_active",
]
COLUMNS = ["id", *FIELDS, "created_at", "updated_at"]
BOOL_FIELDS = ["is_active"]


def _as_bool(value):
    return None if value is None else bool(value)


@dataclass
class Depot:
    id: int
    depot_code: str
    name: str
    area: Optional[str]
    capacity: int
    latitude: Optional[float]
    longitude: Optional[float]
    is_active: bool
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row) -> "Depot":
        return cls(
            id=row["id"],
            depot_code=row["depot_code"],
            name=row["name"],
            area=row["area"],
            capacity=row["capacity"],
            latitude=row["latitude"],
            longitude=row["longitude"],
            is_active=_as_bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def to_dict(self) -> dict:
        return asdict(self)
