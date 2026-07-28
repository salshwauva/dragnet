"""SQLite store for seen-postings + lightweight run history.

Schema: one table, `postings(fingerprint TEXT PRIMARY KEY, first_seen TEXT,
last_seen TEXT, source TEXT, title TEXT, company TEXT, url TEXT, score REAL)`.
A second table `runs(id INTEGER, ran_at TEXT, total INTEGER, new INTEGER)` for
operational sanity checks.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from dragnet.models import Posting

SCHEMA = """
CREATE TABLE IF NOT EXISTS postings (
    fingerprint TEXT PRIMARY KEY,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    source TEXT,
    title TEXT,
    company TEXT,
    url TEXT,
    score REAL
);
CREATE INDEX IF NOT EXISTS idx_postings_last_seen ON postings(last_seen);
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ran_at TEXT NOT NULL,
    total INTEGER,
    new_postings INTEGER
);
"""


class SeenStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.conn = sqlite3.connect(str(path))
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def contains_many(self, fingerprints: list[str]) -> set[str]:
        """Return the subset of `fingerprints` we've already seen."""
        if not fingerprints:
            return set()
        # SQLite caps parameters at ~999; chunk to be safe.
        seen: set[str] = set()
        for i in range(0, len(fingerprints), 500):
            chunk = fingerprints[i : i + 500]
            placeholders = ",".join("?" * len(chunk))
            rows = self.conn.execute(
                f"SELECT fingerprint FROM postings WHERE fingerprint IN ({placeholders})",
                chunk,
            ).fetchall()
            seen.update(r[0] for r in rows)
        return seen

    def upsert_many(self, postings: list[Posting]) -> None:
        """Insert new postings or refresh last_seen on already-seen ones."""
        now = datetime.now(UTC).isoformat()
        rows = [
            (
                p.fingerprint,
                now,
                now,
                p.source,
                p.title[:300],
                p.company[:200],
                p.url[:500],
                p.score,
            )
            for p in postings
        ]
        self.conn.executemany(
            """INSERT INTO postings (fingerprint, first_seen, last_seen, source,
                                     title, company, url, score)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(fingerprint) DO UPDATE SET last_seen=excluded.last_seen,
                                                      score=excluded.score""",
            rows,
        )
        self.conn.commit()

    def record_run(self, total: int, new_count: int) -> None:
        self.conn.execute(
            "INSERT INTO runs (ran_at, total, new_postings) VALUES (?, ?, ?)",
            (datetime.now(UTC).isoformat(), total, new_count),
        )
        self.conn.commit()
