"""Buses data model.

Individual buses in the fleet.

Table: buses
"""
from dataclasses import asdict, dataclass
from typing import Optional

TABLE = "buses"

BUS_TYPE_CHOICES = ('ordinary', 'ac', 'electric', 'midi',)

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS buses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    registration_no TEXT NOT NULL UNIQUE,
    depot_id INTEGER NOT NULL REFERENCES depots(id),
    capacity INTEGER DEFAULT 60,
    bus_type TEXT DEFAULT 'ordinary',
    manufacture_year INTEGER,
    is_operational INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_buses_depot_id ON buses (depot_id);",
    "CREATE INDEX IF NOT EXISTS idx_buses_bus_type ON buses (bus_type);",
]

FIELDS = [
    "registration_no",
    "depot_id",
    "capacity",
    "bus_type",
    "manufacture_year",
    "is_operational",
]
COLUMNS = ["id", *FIELDS, "created_at", "updated_at"]
BOOL_FIELDS = ["is_operational"]


def _as_bool(value):
    return None if value is None else bool(value)


@dataclass
class Bus:
    id: int
    registration_no: str
    depot_id: int
    capacity: int
    bus_type: str
    manufacture_year: Optional[int]
    is_operational: bool
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row) -> "Bus":
        return cls(
            id=row["id"],
            registration_no=row["registration_no"],
            depot_id=row["depot_id"],
            capacity=row["capacity"],
            bus_type=row["bus_type"],
            manufacture_year=row["manufacture_year"],
            is_operational=_as_bool(row["is_operational"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def to_dict(self) -> dict:
        return asdict(self)
