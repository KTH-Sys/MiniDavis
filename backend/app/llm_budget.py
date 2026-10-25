"""Persistent shared request reservations; no credentials or prompts are stored."""

import math
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock

from .config import Settings
from .schemas import ProviderUsage


class Budget:
    def __init__(self, path: Path, settings: Settings, clock=time.time):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False, timeout=10)
        self.lock = RLock()
        self.settings, self.clock = settings, clock
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS llm_calls (
                id INTEGER PRIMARY KEY, day TEXT, run_id TEXT, agent_id TEXT, at REAL,
                reserved INTEGER, tokens INTEGER DEFAULT 0, status TEXT DEFAULT 'pending');
            CREATE INDEX IF NOT EXISTS llm_day ON llm_calls(day, at);
            CREATE TABLE IF NOT EXISTS llm_cooldown (id INTEGER PRIMARY KEY, until REAL);
            INSERT OR IGNORE INTO llm_cooldown VALUES (1, 0);
        ''')

    def _day(self, now):
        return datetime.fromtimestamp(now, timezone.utc).date().isoformat()

    def reserve(self, run_id: str, agent_id: str, tokens: int) -> tuple[int | None, str]:
        now, s = self.clock(), self.settings
        with self.lock:
            self.db.execute('BEGIN IMMEDIATE')
            try:
                # A crashed worker's lease expires, but its conservative token charge remains.
                self.db.execute("UPDATE llm_calls SET status='abandoned' WHERE status='pending' AND at < ?",
                                (now - s.llm_timeout_seconds - 5,))
                rows = self.db.execute('SELECT run_id, agent_id, at, reserved, status FROM llm_calls WHERE day=?',
                                       (self._day(now),)).fetchall()
                run_calls = self.db.execute('SELECT count(*) FROM llm_calls WHERE run_id=?', (run_id,)).fetchone()[0]
                cooldown = self.db.execute('SELECT until FROM llm_cooldown WHERE id=1').fetchone()[0]
                pending = self.db.execute("SELECT count(*) FROM llm_calls WHERE status='pending'").fetchone()[0]
                last = self.db.execute('SELECT max(at) FROM llm_calls').fetchone()[0]
                minute = self.db.execute('SELECT count(*) FROM llm_calls WHERE at > ?', (now-60,)).fetchone()[0]
                resident_last = self.db.execute('SELECT max(at) FROM llm_calls WHERE run_id=? AND agent_id=?',
                                                (run_id, agent_id)).fetchone()[0]
                reason = ''
                if cooldown > now: reason = 'Provider cooldown (Retry-After)'
                elif pending: reason = 'Another resident is awaiting Groq'
                elif run_calls >= s.llm_max_calls_per_run: reason = 'Run request budget exhausted'
                elif len(rows) >= s.llm_max_calls_per_day: reason = 'Daily request budget exhausted'
                elif sum(row[3] for row in rows) + tokens > s.llm_max_tokens_per_day: reason = 'Daily token budget exhausted'
                elif minute >= s.llm_max_requests_per_minute: reason = 'Shared request queue'
                elif last is not None and now - last < 60 / s.llm_max_requests_per_minute: reason = 'Shared request queue'
                elif resident_last is not None and now - resident_last < s.llm_min_agent_replan_seconds: reason = 'Resident replan cooldown'
                if reason:
                    self.db.commit()
                    return None, reason
                cursor = self.db.execute('INSERT INTO llm_calls(day,run_id,agent_id,at,reserved) VALUES(?,?,?,?,?)',
                                         (self._day(now), run_id, agent_id, now, tokens))
                self.db.commit()
                return cursor.lastrowid, ''
            except Exception:
                self.db.rollback()
                raise

    def finish(self, call_id: int, tokens: int | None, status: str, retry_after: float = 0):
        with self.lock, self.db:
            # Unknown usage keeps its full reservation. Failed/retried calls still count.
            if tokens is None:
                self.db.execute('UPDATE llm_calls SET status=? WHERE id=?', (status, call_id))
            else:
                self.db.execute('UPDATE llm_calls SET status=?,tokens=?,reserved=? WHERE id=?',
                                (status, tokens, tokens, call_id))
            if retry_after:
                self.db.execute('UPDATE llm_cooldown SET until=max(until,?) WHERE id=1',
                                (self.clock() + retry_after,))

    def usage(self, run_id: str) -> ProviderUsage:
        now = self.clock()
        with self.lock:
            calls, reserved, tokens = self.db.execute(
                'SELECT count(*),coalesce(sum(reserved),0),coalesce(sum(tokens),0) FROM llm_calls WHERE day=?',
                (self._day(now),)).fetchone()
            run = self.db.execute('SELECT count(*) FROM llm_calls WHERE run_id=?', (run_id,)).fetchone()[0]
            until = self.db.execute('SELECT until FROM llm_cooldown WHERE id=1').fetchone()[0]
        return ProviderUsage(calls_run=run, calls_day=calls, tokens_day=tokens,
                             reserved_tokens_day=reserved, cooldown_seconds=max(0, math.ceil(until-now)))

    def close(self):
        with self.lock:
            self.db.close()
