"""Durable event store: every town event saved to SQLite so it survives a restart."""

import json
import math
import re
import sqlite3
from functools import lru_cache
from hashlib import sha256
from importlib.util import find_spec
from pathlib import Path
from threading import RLock

from .schemas import Event, MemoryContext

FIELDS = list(Event.model_fields)
MINILM_REVISION = '1110a243fdf4706b3f48f1d95db1a4f5529b4d41'


class EventStore:
    def __init__(self, path: str | Path, embedder=None, embedding_key: str | None = None):
        """embedder: optional callable(list[str]) -> list[vector], e.g. minilm_embedder()."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._embedder = embedder
        self._embedding_key = embedding_key or getattr(embedder, 'cache_key', 'custom-embedder-v1')
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS events ("
            "event_id TEXT PRIMARY KEY, run_id TEXT, tick INTEGER, agent_id TEXT,"
            " action TEXT, outcome TEXT, text TEXT)"
        )
        self.db.execute("CREATE INDEX IF NOT EXISTS events_scope ON events(run_id, agent_id, tick)")
        # The old event-ID-only cache is deliberately left unused: its vectors
        # cannot be attributed to a model or to the current source text.
        self.db.execute("CREATE TABLE IF NOT EXISTS memory_vectors ("
                        "model_key TEXT, event_id TEXT, text_sha256 TEXT, vector TEXT,"
                        " PRIMARY KEY(model_key, event_id))")

    def warmup(self) -> None:
        """Load optional weights during app startup, before the world serves ticks."""
        if self._embedder and hasattr(self._embedder, 'warmup'):
            try:
                self._embedder.warmup()
            except Exception:
                self._embedder = None  # labelled lexical fallback, no retry loop per tick

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
        query_batch = self._embedder([query])
        if len(query_batch) != 1:
            raise ValueError('Invalid query embedding batch')
        query_vector = checked_vector(query_batch[0])
        if any(len(vector) != len(query_vector) for vector in vectors.values()):
            raise ValueError('Embedding dimensions differ')
        ranked = [(cosine(query_vector, vectors[e.event_id]), e.tick, e.event_id, e) for e in eligible]
        ranked = sorted((item for item in ranked if item[0] > 0), key=lambda item: item[:3], reverse=True)
        return [item[3] for item in ranked[:3]]

    def _vectors(self, events: list[Event]) -> dict[str, list[float]]:
        """Embed each event once; later calls read the vector back from SQLite."""
        ids = [e.event_id for e in events]
        with self._lock:
            rows = self.db.execute(
                f"SELECT event_id, text_sha256, vector FROM memory_vectors WHERE model_key = ?"
                f" AND event_id IN ({','.join('?' * len(ids))})", [self._embedding_key, *ids]
            ).fetchall()
        hashes = {event.event_id: sha256(event.text.encode()).hexdigest() for event in events}
        vectors = {}
        for event_id, text_hash, vector in rows:
            if hashes[event_id] != text_hash:
                continue
            try:
                vectors[event_id] = checked_vector(json.loads(vector))
            except (ValueError, TypeError):
                continue
        missing = [e for e in events if e.event_id not in vectors]
        if missing:
            batch = self._embedder([e.text for e in missing])
            if len(batch) != len(missing):
                raise ValueError('Invalid event embedding batch')
            new = [checked_vector(vector) for vector in batch]
            with self._lock, self.db:
                self.db.executemany("INSERT OR REPLACE INTO memory_vectors VALUES (?, ?, ?, ?)",
                                    [(self._embedding_key, e.event_id, hashes[e.event_id], json.dumps(v))
                                     for e, v in zip(missing, new)])
            vectors.update({e.event_id: v for e, v in zip(missing, new)})
        return vectors

    def close(self) -> None:
        with self._lock:
            self.db.close()


def cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError('Embedding dimensions differ')
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return sum(x * y for x, y in zip(a, b)) / norm if norm else 0.0


def checked_vector(vector) -> list[float]:
    if not isinstance(vector, (list, tuple)) or not vector:
        raise ValueError('Embedding must be a nonempty numeric vector')
    if any(type(value) not in (int, float) or not math.isfinite(value) for value in vector):
        raise ValueError('Embedding contains nonfinite or nonnumeric values')
    return [float(value) for value in vector]


class MiniLMEmbedder:
    def __init__(self, model_name, cache_folder, revision):
        self.model_name, self.cache_folder, self.revision = model_name, cache_folder, revision
        self.cache_key = f'sentence-transformers:{model_name}:{revision}:normalized-v1'
        self.model = None
        self.lock = RLock()

    def warmup(self):
        with self.lock:
            if self.model is None:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(self.model_name, device='cpu', cache_folder=self.cache_folder,
                                                 revision=self.revision)

    def __call__(self, texts):
        self.warmup()
        with self.lock:
            return self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False).tolist()


@lru_cache(maxsize=2)
def minilm_embedder(model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
                    cache_folder: str = 'data/model-cache', revision: str = MINILM_REVISION):
    """Return a CPU MiniLM embedder, or None when sentence-transformers is not installed.

    The model loads on first use (about 90 MB, cached by Hugging Face after that).
    """
    if find_spec('sentence_transformers') is None:
        return None
    return MiniLMEmbedder(model_name, cache_folder, revision)
