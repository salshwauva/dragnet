"""SQLite store for seen-postings, posting lifecycle, and lightweight run history.

Schema: `postings(fingerprint TEXT PRIMARY KEY, first_seen, last_seen, source, title,
company, url, score, full_text, status, closed_at, missed_runs)`,
`skills(id, name, category)` and `posting_skills(fingerprint, skill_id)` for extracted
skills, plus `runs(id, ran_at, total, new_postings)` for operational sanity checks.

Lifecycle: a row is `active` while its source keeps returning it. Each successful
crawl of a source that omits the row bumps `missed_runs`; once that reaches the
configured threshold the row becomes `inactive` and `closed_at` is set. A row that
comes back is reactivated in place: `missed_runs` and `closed_at` reset, `first_seen`
is kept. This is an observed lifecycle, not the employer's real open/close dates.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
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
    score REAL,
    full_text TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    closed_at TEXT,
    missed_runs INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_postings_last_seen ON postings(last_seen);
CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS posting_skills (
    fingerprint TEXT NOT NULL REFERENCES postings(fingerprint),
    skill_id INTEGER NOT NULL REFERENCES skills(id),
    UNIQUE(fingerprint, skill_id)
);
CREATE INDEX IF NOT EXISTS idx_posting_skills_skill ON posting_skills(skill_id);
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ran_at TEXT NOT NULL,
    total INTEGER,
    new_postings INTEGER
);
"""

# Columns added after the first release. Applied with ALTER TABLE when an older
# database is opened, so the live dragnet.db migrates in place.
_MIGRATIONS: list[tuple[str, str]] = [
    ("full_text", "TEXT NOT NULL DEFAULT ''"),
    ("status", "TEXT NOT NULL DEFAULT 'active'"),
    ("closed_at", "TEXT"),
    ("missed_runs", "INTEGER NOT NULL DEFAULT 0"),
]


@dataclass(frozen=True)
class PostingRecord:
    """Read-only view of one stored row. What tests and analytics see instead of SQL."""

    fingerprint: str
    source: str
    first_seen: datetime
    last_seen: datetime
    status: str
    closed_at: datetime | None
    missed_runs: int
    full_text: str


def _now() -> str:
    return datetime.now(UTC).isoformat()


class SeenStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.conn = sqlite3.connect(str(path))
        self.conn.executescript(SCHEMA)
        self._migrate()
        self.conn.commit()

    def _migrate(self) -> None:
        have = {row[1] for row in self.conn.execute("PRAGMA table_info(postings)")}
        for column, decl in _MIGRATIONS:
            if column not in have:
                self.conn.execute(f"ALTER TABLE postings ADD COLUMN {column} {decl}")
        # Indexed after migration: older files lack the column until the ALTER runs.
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_postings_status ON postings(status)")

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

    def get(self, fingerprint: str) -> PostingRecord | None:
        row = self.conn.execute(
            """SELECT fingerprint, source, first_seen, last_seen, status, closed_at,
                      missed_runs, full_text
               FROM postings WHERE fingerprint = ?""",
            (fingerprint,),
        ).fetchone()
        if row is None:
            return None
        return PostingRecord(
            fingerprint=row[0],
            source=row[1],
            first_seen=datetime.fromisoformat(row[2]),
            last_seen=datetime.fromisoformat(row[3]),
            status=row[4],
            closed_at=datetime.fromisoformat(row[5]) if row[5] else None,
            missed_runs=row[6],
            full_text=row[7],
        )

    def count(self, status: str | None = None) -> int:
        if status is None:
            row = self.conn.execute("SELECT COUNT(*) FROM postings").fetchone()
        else:
            row = self.conn.execute(
                "SELECT COUNT(*) FROM postings WHERE status = ?", (status,)
            ).fetchone()
        return int(row[0])

    def upsert_many(self, postings: list[Posting]) -> None:
        """Insert new postings or refresh already-seen ones.

        An observed posting is active by definition, so a conflict also clears any
        absence state. first_seen is never touched after insert.
        """
        now = _now()
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
                p.description,
            )
            for p in postings
        ]
        self.conn.executemany(
            """INSERT INTO postings (fingerprint, first_seen, last_seen, source,
                                     title, company, url, score, full_text)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(fingerprint) DO UPDATE SET
                   last_seen=excluded.last_seen,
                   score=excluded.score,
                   full_text=CASE WHEN excluded.full_text != '' THEN excluded.full_text
                                  ELSE full_text END,
                   status='active',
                   closed_at=NULL,
                   missed_runs=0""",
            rows,
        )
        self.conn.commit()

    def mark_absent(self, observed: set[str], sources: set[str], threshold: int) -> int:
        """Age active postings that a successful crawl did not return.

        Only rows whose source is in `sources` are touched: a source that crashed or
        was disabled this run says nothing about its postings. Returns the number of
        rows that crossed `threshold` and became inactive.
        """
        if not sources:
            return 0
        now = _now()
        # Observed set can exceed the parameter limit, so stage it in a temp table.
        self.conn.execute("CREATE TEMP TABLE IF NOT EXISTS observed (fingerprint TEXT PRIMARY KEY)")
        self.conn.execute("DELETE FROM observed")
        self.conn.executemany(
            "INSERT OR IGNORE INTO observed (fingerprint) VALUES (?)",
            [(fp,) for fp in observed],
        )
        src_placeholders = ",".join("?" * len(sources))
        src_params = tuple(sources)
        self.conn.execute(
            f"""UPDATE postings SET missed_runs = missed_runs + 1
                WHERE status = 'active'
                  AND source IN ({src_placeholders})
                  AND fingerprint NOT IN (SELECT fingerprint FROM observed)""",
            src_params,
        )
        cur = self.conn.execute(
            f"""UPDATE postings SET status = 'inactive', closed_at = ?
                WHERE status = 'active'
                  AND source IN ({src_placeholders})
                  AND missed_runs >= ?""",
            (now, *src_params, threshold),
        )
        self.conn.commit()
        return cur.rowcount

    def save_skills(self, skills_by_posting: dict[str, list[tuple[str, str]]]) -> None:
        """Replace each posting's skill set with the given (name, category) pairs.

        A rerun with a changed vocabulary drops stale rows and adds new ones, so the
        join table always mirrors the current extractor output.
        """
        for fingerprint, pairs in skills_by_posting.items():
            self.conn.executemany(
                "INSERT OR IGNORE INTO skills (name, category) VALUES (?, ?)", pairs
            )
            self.conn.execute("DELETE FROM posting_skills WHERE fingerprint = ?", (fingerprint,))
            self.conn.executemany(
                """INSERT OR IGNORE INTO posting_skills (fingerprint, skill_id)
                   SELECT ?, id FROM skills WHERE name = ?""",
                [(fingerprint, name) for name, _ in pairs],
            )
        self.conn.commit()

    def skills_for(self, fingerprint: str) -> list[str]:
        rows = self.conn.execute(
            """SELECT s.name FROM posting_skills ps JOIN skills s ON s.id = ps.skill_id
               WHERE ps.fingerprint = ? ORDER BY s.name""",
            (fingerprint,),
        ).fetchall()
        return [str(r[0]) for r in rows]

    def record_run(self, total: int, new_count: int) -> None:
        self.conn.execute(
            "INSERT INTO runs (ran_at, total, new_postings) VALUES (?, ?, ?)",
            (_now(), total, new_count),
        )
        self.conn.commit()
