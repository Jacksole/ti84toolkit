"""
History/persistence -- logs every calculation to a local SQLite database so
past results survive between sessions. This was explicitly impossible on the
original TI-84 hardware ("No persistent storage after RAM reset" in the V1
Known Limitations); on a real filesystem it's a small module.

Database lives at ~/.ti84toolkit/history.db by default (override via the
TI84TOOLKIT_DB_PATH environment variable, mainly for testing).
"""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


def _db_path() -> Path:
    override = os.environ.get("TI84TOOLKIT_DB_PATH")
    if override:
        return Path(override)
    return Path.home() / ".ti84toolkit" / "history.db"


@contextmanager
def _connect():
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS calculations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                module TEXT NOT NULL,
                operation TEXT NOT NULL,
                inputs TEXT NOT NULL,
                result TEXT NOT NULL
            )
            """
        )
        yield conn
        conn.commit()
    finally:
        conn.close()


@dataclass
class HistoryEntry:
    id: int
    timestamp: str
    module: str
    operation: str
    inputs: dict
    result: str


def log_entry(module: str, operation: str, inputs: dict, result: str) -> None:
    """Record a single calculation. Failures here are swallowed (best-effort
    logging shouldn't break a calculation the user is waiting on)."""
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO calculations (timestamp, module, operation, inputs, result) VALUES (?, ?, ?, ?, ?)",
                (
                    datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    module,
                    operation,
                    json.dumps(inputs, default=str),
                    result,
                ),
            )
    except sqlite3.Error:
        pass


def get_history(limit: int = 20, module: str | None = None) -> list[HistoryEntry]:
    """Return the most recent `limit` calculations, optionally filtered by module."""
    with _connect() as conn:
        if module:
            rows = conn.execute(
                "SELECT id, timestamp, module, operation, inputs, result FROM calculations "
                "WHERE module = ? ORDER BY id DESC LIMIT ?",
                (module, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, timestamp, module, operation, inputs, result FROM calculations "
                "ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()

    return [
        HistoryEntry(id=r[0], timestamp=r[1], module=r[2], operation=r[3], inputs=json.loads(r[4]), result=r[5])
        for r in rows
    ]


def count_entries() -> int:
    with _connect() as conn:
        row = conn.execute("SELECT COUNT(*) FROM calculations").fetchone()
    return row[0] if row else 0


def clear_history() -> int:
    """Delete all history. Returns the number of rows removed."""
    with _connect() as conn:
        count = conn.execute("SELECT COUNT(*) FROM calculations").fetchone()[0]
        conn.execute("DELETE FROM calculations")
    return count
