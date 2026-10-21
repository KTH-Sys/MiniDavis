"""Durable event store: every town event saved to SQLite so it survives a restart."""

import sqlite3
from pathlib import Path

from .schemas import Event

FIELDS = list(Event.model_fields)


class EventStore:
    def __init__(self, path: str | Path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS events ("
            "event_id TEXT PRIMARY KEY, run_id TEXT, tick INTEGER, agent_id TEXT,"
            " action TEXT, outcome TEXT, text TEXT)"
        )

    def save(self, event: Event) -> None:
        row = event.model_dump()
        with self.db:
            self.db.execute(
                f"INSERT OR REPLACE INTO events ({','.join(FIELDS)}) VALUES ({','.join('?' * len(FIELDS))})",
                [row[name] for name in FIELDS],
            )

    def get(self, event_id: str) -> Event | None:
        row = self.db.execute(f"SELECT {','.join(FIELDS)} FROM events WHERE event_id = ?", (event_id,)).fetchone()
        return Event(**dict(zip(FIELDS, row))) if row else None
