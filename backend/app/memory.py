"""Durable event store: every town event saved to SQLite so it survives a restart."""

import re
import sqlite3
from pathlib import Path
from threading import RLock

from .schemas import Event, MemoryContext

FIELDS = list(Event.model_fields)


class EventStore:
    def __init__(self, path: str | Path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS events ("
            "event_id TEXT PRIMARY KEY, run_id TEXT, tick INTEGER, agent_id TEXT,"
            " action TEXT, outcome TEXT, text TEXT)"
        )
        self.db.execute("CREATE INDEX IF NOT EXISTS events_scope ON events(run_id, agent_id, tick)")

    def save(self, event: Event) -> None:
        self.save_many([event])

    def save_many(self, events: list[Event]) -> None:
        """Commit a tick together, so a failed write leaves no partial history."""
        with self._lock, self.db:
            self.db.executemany(
                f"INSERT OR REPLACE INTO events ({','.join(FIELDS)}) VALUES ({','.join('?' * len(FIELDS))})",
                [[getattr(event, name) for name in FIELDS] for event in events],
            )

    def get(self, event_id: str) -> Event | None:
        with self._lock:
            row = self.db.execute(f"SELECT {','.join(FIELDS)} FROM events WHERE event_id = ?", (event_id,)).fetchone()
        return Event(**dict(zip(FIELDS, row))) if row else None

    def recent(self, run_id: str, agent_id: str, limit: int = 5, as_of_tick: int | None = None) -> list[Event]:
        """One resident's newest events in this run, returned oldest first."""
        with self._lock:
            rows = self.db.execute(
                f"SELECT {','.join(FIELDS)} FROM events WHERE run_id = ? AND agent_id = ?"
                " AND (? IS NULL OR tick <= ?) ORDER BY tick DESC, event_id DESC LIMIT ?",
                (run_id, agent_id, as_of_tick, as_of_tick, max(0, min(limit, 500))),
            ).fetchall()
        return [Event(**dict(zip(FIELDS, row))) for row in reversed(rows)]

    def retrieve(self, run_id: str, agent_id: str, query: str, as_of_tick: int) -> MemoryContext:
        """Scoped lexical fallback: no embedding/model download or provider call.

        Rank at most 500 eligible events. Current Event records are resident-private;
        run, resident and observation tick are filtered in SQL before ranking.
        """
        eligible = self.recent(run_id, agent_id, limit=500, as_of_tick=as_of_tick)
        terms = set(re.findall(r"[a-z0-9]+", query.lower()))
        ranked = []
        for event in eligible:
            words = set(re.findall(r"[a-z0-9]+", event.text.lower()))
            score = len(terms & words)
            if score:
                ranked.append((score, event.tick, event.event_id, event))
        ranked.sort(key=lambda item: item[:3], reverse=True)
        return MemoryContext(query=query, as_of_tick=as_of_tick,
                             recent=eligible[-5:], relevant=[item[3] for item in ranked[:3]])

    def close(self) -> None:
        with self._lock:
            self.db.close()
