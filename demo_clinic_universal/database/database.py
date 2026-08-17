from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Iterator


class Database:
    def __init__(self, path: str) -> None:
        self.path = str(Path(path))
        self._lock = RLock()
        self._initialize()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            conn = sqlite3.connect(self.path, timeout=20)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def _initialize(self) -> None:
        with self.connection() as conn:
            conn.executescript(
                """
                PRAGMA journal_mode=WAL;

                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    platform_user_id TEXT NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    phone TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(platform, platform_user_id)
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    platform_user_id TEXT NOT NULL,
                    current_state TEXT NOT NULL,
                    service_id TEXT,
                    desired_date TEXT,
                    name TEXT,
                    phone TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(platform, platform_user_id)
                );

                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    platform_user_id TEXT NOT NULL,
                    service_id TEXT NOT NULL,
                    service_name TEXT NOT NULL,
                    desired_date TEXT NOT NULL,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    username TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    processed_at TEXT
                );
                """
            )

    @staticmethod
    def now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def upsert_user(
        self,
        platform: str,
        platform_user_id: str,
        username: str | None,
        first_name: str | None,
        phone: str | None = None,
    ) -> None:
        timestamp = self.now()
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO users(platform, platform_user_id, username, first_name, phone, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(platform, platform_user_id) DO UPDATE SET
                    username=excluded.username,
                    first_name=excluded.first_name,
                    phone=COALESCE(excluded.phone, users.phone),
                    updated_at=excluded.updated_at
                """,
                (platform, platform_user_id, username, first_name, phone, timestamp, timestamp),
            )

    def get_session(self, platform: str, platform_user_id: str) -> sqlite3.Row | None:
        with self.connection() as conn:
            return conn.execute(
                "SELECT * FROM sessions WHERE platform=? AND platform_user_id=?",
                (platform, platform_user_id),
            ).fetchone()

    def upsert_session(self, platform: str, platform_user_id: str, **fields: object) -> None:
        current = self.get_session(platform, platform_user_id)
        timestamp = self.now()
        if current:
            allowed = {"current_state", "service_id", "desired_date", "name", "phone"}
            updates = {k: v for k, v in fields.items() if k in allowed}
            updates["updated_at"] = timestamp
            set_clause = ", ".join(f"{key}=?" for key in updates)
            values = list(updates.values()) + [current["id"]]
            with self.connection() as conn:
                conn.execute(f"UPDATE sessions SET {set_clause} WHERE id=?", values)
            return

        values = {
            "current_state": "idle",
            "service_id": None,
            "desired_date": None,
            "name": None,
            "phone": None,
        }
        values.update({k: v for k, v in fields.items() if k in values})
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO sessions(platform, platform_user_id, current_state, service_id, desired_date, name, phone, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    platform,
                    platform_user_id,
                    values["current_state"],
                    values["service_id"],
                    values["desired_date"],
                    values["name"],
                    values["phone"],
                    timestamp,
                    timestamp,
                ),
            )

    def clear_session(self, platform: str, platform_user_id: str) -> None:
        with self.connection() as conn:
            conn.execute(
                "DELETE FROM sessions WHERE platform=? AND platform_user_id=?",
                (platform, platform_user_id),
            )

    def create_application(
        self,
        platform: str,
        platform_user_id: str,
        service_id: str,
        service_name: str,
        desired_date: str,
        name: str,
        phone: str,
        username: str | None,
    ) -> int:
        timestamp = self.now()
        with self.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO applications(
                    platform, platform_user_id, service_id, service_name,
                    desired_date, name, phone, username, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'new', ?)
                """,
                (
                    platform,
                    platform_user_id,
                    service_id,
                    service_name,
                    desired_date,
                    name,
                    phone,
                    username,
                    timestamp,
                ),
            )
            return int(cursor.lastrowid)

    def get_application(self, application_id: int) -> sqlite3.Row | None:
        with self.connection() as conn:
            return conn.execute("SELECT * FROM applications WHERE id=?", (application_id,)).fetchone()

    def update_application_status(self, application_id: int, status: str) -> bool:
        with self.connection() as conn:
            cursor = conn.execute(
                "UPDATE applications SET status=?, processed_at=? WHERE id=? AND status='new'",
                (status, self.now(), application_id),
            )
            return cursor.rowcount == 1
