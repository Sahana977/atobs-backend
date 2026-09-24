"""Small date/time helpers shared across the app."""
from datetime import datetime, timedelta


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


def add_minutes(value: str, minutes: float) -> str:
    return (parse_iso(value) + timedelta(minutes=minutes)).isoformat(timespec="seconds")
