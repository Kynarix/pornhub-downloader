from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

from core.settings import DATA_DIR


class HistoryStore:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or (DATA_DIR / "history.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS history (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    filepath TEXT,
                    format_label TEXT,
                    status TEXT,
                    created_at REAL,
                    meta_json TEXT
                )
                """
            )
            conn.commit()

    def add(self, job: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO history
                (id, title, url, filepath, format_label, status, created_at, meta_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.get("id"),
                    job.get("title", ""),
                    job.get("url", ""),
                    job.get("filepath", ""),
                    job.get("format_label", ""),
                    job.get("status", ""),
                    time.time(),
                    json.dumps(job, ensure_ascii=False),
                ),
            )
            conn.commit()

    def list(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, title, url, filepath, format_label, status, created_at
                FROM history
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def clear(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM history")
            conn.commit()
