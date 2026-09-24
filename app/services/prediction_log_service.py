"""Stores every prediction/route request so you can review what the API returned."""
import json

from app import database
from app.utils.time_utils import now_iso


def log(kind: str, request: dict, response: dict) -> None:
    with database.session() as conn:
        conn.execute(
            "INSERT INTO prediction_log (created_at, kind, request, response) VALUES (?, ?, ?, ?)",
            (now_iso(), kind, json.dumps(request, default=str), json.dumps(response, default=str)),
        )


def recent(limit: int = 20, kind: str | None = None) -> list[dict]:
    sql = "SELECT id, created_at, kind, request, response FROM prediction_log"
    params: list = []
    if kind:
        sql += " WHERE kind = ?"
        params.append(kind)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    with database.session() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [{"id": r["id"], "created_at": r["created_at"], "kind": r["kind"],
             "request": json.loads(r["request"]), "response": json.loads(r["response"])} for r in rows]


def clear() -> int:
    with database.session() as conn:
        return conn.execute("DELETE FROM prediction_log").rowcount
