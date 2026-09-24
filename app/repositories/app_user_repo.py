"""Data access for users — plain SQL on sqlite3, no ORM."""
import sqlite3
from typing import Optional

from app.models.app_user import COLUMNS, TABLE, AppUser
from app.utils.time_utils import now_iso

SORTABLE = set(COLUMNS)


def _to_db_bool(value):
    return None if value is None else int(bool(value))


def create(conn: sqlite3.Connection, data: dict) -> AppUser:
    ts = now_iso()
    cur = conn.execute(
        "INSERT INTO app_users ("
        "email, full_name, role, home_stop_id, is_active, created_at, updated_at"
        ") VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            data.get("email"),
            data.get("full_name"),
            data.get("role", 'commuter'),
            data.get("home_stop_id"),
            _to_db_bool(data.get("is_active", True)),
            ts,
            ts,
        ),
    )
    return get(conn, cur.lastrowid)


def get(conn: sqlite3.Connection, item_id: int) -> Optional[AppUser]:
    row = conn.execute("SELECT * FROM app_users WHERE id = ?", (item_id,)).fetchone()
    return AppUser.from_row(row) if row else None


def get_by_email(conn: sqlite3.Connection, value) -> Optional[AppUser]:
    row = conn.execute("SELECT * FROM app_users WHERE email = ?", (value,)).fetchone()
    return AppUser.from_row(row) if row else None


def exists(conn: sqlite3.Connection, item_id: int) -> bool:
    return conn.execute("SELECT 1 FROM app_users WHERE id = ?", (item_id,)).fetchone() is not None


def _where(filters: Optional[dict]) -> tuple[str, list]:
    filters = filters or {}
    clauses: list[str] = []
    params: list = []
    if filters.get("email") is not None:
        clauses.append("email = ?")
        params.append(filters["email"])
    if filters.get("role") is not None:
        clauses.append("role = ?")
        params.append(filters["role"])
    if filters.get("home_stop_id") is not None:
        clauses.append("home_stop_id = ?")
        params.append(filters["home_stop_id"])
    if filters.get("is_active") is not None:
        clauses.append("is_active = ?")
        params.append(_to_db_bool(filters["is_active"]))
    if filters.get("q"):
        clauses.append("(full_name LIKE ?)")
        like = f"%{filters['q']}%"
        params.extend([like] * 1)
    sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return sql, params


def list_(conn: sqlite3.Connection, filters: Optional[dict] = None, limit: int = 50, offset: int = 0,
          order_by: str = "id", descending: bool = False) -> list[AppUser]:
    if order_by not in SORTABLE:
        order_by = "id"
    where, params = _where(filters)
    direction = "DESC" if descending else "ASC"
    sql = f"SELECT * FROM app_users{where} ORDER BY {order_by} {direction} LIMIT ? OFFSET ?"
    rows = conn.execute(sql, [*params, limit, offset]).fetchall()
    return [AppUser.from_row(r) for r in rows]


def count(conn: sqlite3.Connection, filters: Optional[dict] = None) -> int:
    where, params = _where(filters)
    return conn.execute(f"SELECT COUNT(*) FROM app_users{where}", params).fetchone()[0]


def update(conn: sqlite3.Connection, item_id: int, changes: dict) -> Optional[AppUser]:
    allowed = {}
    if changes.get("email") is not None:
        allowed["email"] = changes["email"]
    if changes.get("full_name") is not None:
        allowed["full_name"] = changes["full_name"]
    if changes.get("role") is not None:
        allowed["role"] = changes["role"]
    if changes.get("home_stop_id") is not None:
        allowed["home_stop_id"] = changes["home_stop_id"]
    if changes.get("is_active") is not None:
        allowed["is_active"] = _to_db_bool(changes["is_active"])
    if not allowed:
        return get(conn, item_id)
    assignments = ", ".join(f"{column} = ?" for column in allowed)
    conn.execute(
        f"UPDATE app_users SET {assignments}, updated_at = ? WHERE id = ?",
        [*allowed.values(), now_iso(), item_id],
    )
    return get(conn, item_id)


def delete(conn: sqlite3.Connection, item_id: int) -> bool:
    cur = conn.execute("DELETE FROM app_users WHERE id = ?", (item_id,))
    return cur.rowcount > 0


def bulk_create(conn: sqlite3.Connection, items: list[dict]) -> list[AppUser]:
    return [create(conn, item) for item in items]
