"""Users data model.

Commuters, operators and admins.

Table: app_users
"""
from dataclasses import asdict, dataclass
from typing import Optional

TABLE = "app_users"

ROLE_CHOICES = ('commuter', 'operator', 'admin',)

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS app_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    role TEXT DEFAULT 'commuter',
    home_stop_id INTEGER REFERENCES stops(id),
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_app_users_role ON app_users (role);",
    "CREATE INDEX IF NOT EXISTS idx_app_users_home_stop_id ON app_users (home_stop_id);",
]

FIELDS = [
    "email",
    "full_name",
    "role",
    "home_stop_id",
    "is_active",
]
COLUMNS = ["id", *FIELDS, "created_at", "updated_at"]
BOOL_FIELDS = ["is_active"]


def _as_bool(value):
    return None if value is None else bool(value)


@dataclass
class AppUser:
    id: int
    email: str
    full_name: str
    role: str
    home_stop_id: Optional[int]
    is_active: bool
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row) -> "AppUser":
        return cls(
            id=row["id"],
            email=row["email"],
            full_name=row["full_name"],
            role=row["role"],
            home_stop_id=row["home_stop_id"],
            is_active=_as_bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def to_dict(self) -> dict:
        return asdict(self)
