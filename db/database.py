import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional, Tuple

DB_FILENAME = "history.sqlite3"


def _get_db_path() -> str:
    base_dir = Path(__file__).resolve().parent.parent
    db_dir = base_dir / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    return str(db_dir / DB_FILENAME)


@contextmanager
def _connect() -> Iterable[sqlite3.Connection]:
    conn = sqlite3.connect(_get_db_path())
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS request_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                request_type TEXT NOT NULL,
                query TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def save_request(
    user_id: int,
    request_type: str,
    query: str,
    created_at: Optional[datetime] = None,
) -> None:
    created_at = created_at or datetime.utcnow()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO request_history (user_id, request_type, query, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, request_type, query, created_at.isoformat()),
        )


def get_last_requests(user_id: int, limit: int = 10) -> Tuple[tuple, ...]:
    with _connect() as conn:
        cursor = conn.execute(
            """
            SELECT request_type, query, created_at
            FROM request_history
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        return cursor.fetchall()
