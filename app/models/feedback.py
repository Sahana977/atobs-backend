"""Feedback data model.

Commuter ratings of trips, including comfort.

Table: feedback
"""
from dataclasses import asdict, dataclass
from typing import Optional

TABLE = "feedback"

CATEGORY_CHOICES = ('crowding', 'delay', 'cleanliness', 'staff', 'other',)

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES app_users(id),
    trip_id INTEGER REFERENCES trips(id),
    rating INTEGER NOT NULL,
    comfort_rating INTEGER,
    category TEXT DEFAULT 'other',
    comment TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback (user_id);",
    "CREATE INDEX IF NOT EXISTS idx_feedback_trip_id ON feedback (trip_id);",
    "CREATE INDEX IF NOT EXISTS idx_feedback_category ON feedback (category);",
]

FIELDS = [
    "user_id",
    "trip_id",
    "rating",
    "comfort_rating",
    "category",
    "comment",
]
COLUMNS = ["id", *FIELDS, "created_at", "updated_at"]
BOOL_FIELDS = []


def _as_bool(value):
    return None if value is None else bool(value)


@dataclass
class Feedback:
    id: int
    user_id: Optional[int]
    trip_id: Optional[int]
    rating: int
    comfort_rating: Optional[int]
    category: str
    comment: Optional[str]
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row) -> "Feedback":
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            trip_id=row["trip_id"],
            rating=row["rating"],
            comfort_rating=row["comfort_rating"],
            category=row["category"],
            comment=row["comment"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def to_dict(self) -> dict:
        return asdict(self)
