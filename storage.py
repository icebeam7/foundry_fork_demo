"""Single-user local SQLite checkpoint store. Never store access tokens."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, path: str):
        self.path = Path(path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as con:
            con.execute("""CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY, created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL, label TEXT NOT NULL,
                payload TEXT NOT NULL
            )""")

    def _connect(self):
        return sqlite3.connect(str(self.path), timeout=15)

    def new(self, label: str = "Northstar financial fork") -> dict:
        run = {
            "id": str(uuid4()), "label": label, "created_at": utcnow(),
            "base": None, "bull": [], "bear": [], "comparison": None,
            "events": [],
        }
        self.save(run)
        return run

    def save(self, run: dict):
        ts = utcnow()
        payload = json.dumps(run, ensure_ascii=False)
        with self._connect() as con:
            con.execute("""INSERT INTO runs(id,created_at,updated_at,label,payload)
                VALUES (?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
                updated_at=excluded.updated_at,label=excluded.label,
                payload=excluded.payload""",
                (run["id"], run["created_at"], ts, run["label"], payload))

    def load(self, run_id: str) -> dict:
        with self._connect() as con:
            row = con.execute("SELECT payload FROM runs WHERE id=?", (run_id,)).fetchone()
        if row is None:
            raise ValueError("Checkpoint does not exist")
        return json.loads(row[0])

    def list_runs(self) -> list[tuple[str, str, str]]:
        with self._connect() as con:
            return con.execute("SELECT id,label,updated_at FROM runs ORDER BY updated_at DESC").fetchall()

    def delete(self, run_id: str):
        with self._connect() as con:
            con.execute("DELETE FROM runs WHERE id=?", (run_id,))
