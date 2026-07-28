# ADR 0003: SQLite for seen-postings; sha1-of-normalized-fields fingerprint dedup

## Status
Accepted — 2026-05-22

## Context
The whole point of the daily brief is "new since last run." That requires persistent state across runs. Without dedup, the same posting would appear in every brief until it expired upstream — which is exactly the failure mode of the prior-art scrapers.

We need a fingerprint that:
- Is stable across cosmetic changes (whitespace, capitalization, punctuation) so a reposted-but-otherwise-same job doesn't show up again.
- Distinguishes truly different postings (same company posting a different role, same role at different company).
- Is computed without any network call.

## Decision
Storage: stdlib `sqlite3`. Single table `postings` with `fingerprint` as PRIMARY KEY plus timestamps and a few metadata fields for debugging. A second table `runs` tracks operational stats.

Fingerprint: `sha1(source | normalized_company | normalized_title | normalized_location)`. Normalization: lowercase, strip punctuation, collapse whitespace, trim. Location truncated to 80 chars to handle "Remote (50 states listed)" cases.

`source` is part of the fingerprint so the same role appearing in Adzuna AND USAJobs counts as two postings — that's intentional, since each surfaces different metadata (USAJobs has the clearance flag, Adzuna has the description snippet) and you may want to evaluate both presentations.

## Consequences
Easier: dedup is local, fast (single index lookup), and stable across reorderings.
Harder: cross-source dedup is intentionally weak — you'll see the same role twice if two sources both list it. Worth it for the metadata diversity.

## Alternatives considered
- **URL as fingerprint.** Rejected: URLs change across reposts (tracking params, A/B test IDs).
- **(company + title) only, ignoring source.** Considered. Rejected because the metadata-diversity argument above outweighs the small duplication cost.
- **A cloud DB (Supabase, Postgres on Fly.io).** Way over-engineered for a personal tool.
