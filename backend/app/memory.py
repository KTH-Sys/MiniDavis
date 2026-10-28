"""Durable event store: every town event saved to SQLite so it survives a restart."""

import json
import math
import re
import sqlite3
from pathlib import Path
from threading import RLock

from .schemas import Event, MemoryContext

FIELDS = list(Event.model_fields)


class EventStore:
    def __init__(self, path: str | Path, embedder=None):
        """embedder: optional callable(list[str]) -> list[vector], e.g. minilm_embedder()."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._embedder = embedder
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS events ("
            "event_id TEXT PRIMARY KEY, run_id TEXT, tick INTEGER, agent_id TEXT,"
            " action TEXT, outcome TEXT, text TEXT)"
        )
        self.db.execute("CREATE INDEX IF NOT EXISTS events_scope ON events(run_id, agent_id, tick)")
        self.db.execute("CREATE TABLE IF NOT EXISTS embeddings (event_id TEXT PRIMARY KEY, vector TEXT)")

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
        """Five recent events plus the top three relevant ones, all scoped in SQL first.

        Run, resident and observation tick are filtered before ranking, so ranking can
        never see another resident's or another run's events. Uses cached MiniLM
        embeddings when available and falls back to keyword search if they fail.
        """
        eligible = self.recent(run_id, agent_id, limit=500, as_of_tick=as_of_tick)
        mode, relevant = "lexical", self._lexical(eligible, query)
        if self._embedder and eligible:
            try:
                mode, relevant = "semantic", self._semantic(eligible, query)
            except Exception:
                pass
        return MemoryContext(mode=mode, query=query, as_of_tick=as_of_tick,
                             recent=eligible[-5:], relevant=relevant)

    def _lexical(self, eligible: list[Event], query: str) -> list[Event]:
        terms = set(re.findall(r"[a-z0-9]+", query.lower()))
        ranked = []
        for event in eligible:
            score = len(terms & set(re.findall(r"[a-z0-9]+", event.text.lower())))
            if score:
                ranked.append((score, event.tick, event.event_id, event))
        ranked.sort(key=lambda item: item[:3], reverse=True)
        return [item[3] for item in ranked[:3]]

    def _semantic(self, eligible: list[Event], query: str) -> list[Event]:
        vectors = self._vectors(eligible)
        query_vector = self._embedder([query])[0]
        ranked = [(cosine(query_vector, vectors[e.event_id]), e.tick, e.event_id, e) for e in eligible]
        ranked = sorted((item for item in ranked if item[0] > 0), key=lambda item: item[:3], reverse=True)
        return [item[3] for item in ranked[:3]]

    def _vectors(self, events: list[Event]) -> dict[str, list[float]]:
        """Embed each event once; later calls read the vector back from SQLite."""
        ids = [e.event_id for e in events]
        with self._lock:
            rows = self.db.execute(
                f"SELECT event_id, vector FROM embeddings WHERE event_id IN ({','.join('?' * len(ids))})", ids
            ).fetchall()
        vectors = {event_id: json.loads(vector) for event_id, vector in rows}
        missing = [e for e in events if e.event_id not in vectors]
        if missing:
            new = [[float(x) for x in v] for v in self._embedder([e.text for e in missing])]
            with self._lock, self.db:
                self.db.executemany("INSERT OR REPLACE INTO embeddings VALUES (?, ?)",
                                    [(e.event_id, json.dumps(v)) for e, v in zip(missing, new)])
            vectors.update({e.event_id: v for e, v in zip(missing, new)})
        return vectors

    def close(self) -> None:
        with self._lock:
            self.db.close()


def cosine(a: list[float], b: list[float]) -> float:
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return sum(x * y for x, y in zip(a, b)) / norm if norm else 0.0


def minilm_embedder(model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
    """Return a CPU MiniLM embedder, or None when sentence-transformers is not installed.

    The model loads on first use (about 90 MB, cached by Hugging Face after that).
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return None
    model = []

    def embed(texts: list[str]) -> list[list[float]]:
        if not model:
            model.append(SentenceTransformer(model_name, device="cpu"))
        return model[0].encode(texts, normalize_embeddings=True).tolist()
    return embed
