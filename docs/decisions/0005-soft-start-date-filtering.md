# ADR 0005: Soft start-date filtering — flag, don't drop

## Status
Accepted — 2026-05-22

## Context
Most internship postings don't include a parseable start date in their structured fields. Some include "Fall 2026" in the body; many include nothing at all; a few are explicitly "Summer 2026 only" — and Sophia's target is Fall 2026.

The naive approach (drop everything without a Fall-2026 match) throws away 80% of legitimate postings. The other naive approach (keep everything) drowns the brief in summer-only roles she can't take.

## Context (extended)
Three classes of postings:
1. **Match.** Body says "Fall 2026" or equivalent. Highest confidence.
2. **Unknown.** No start-date language at all. Most postings live here.
3. **Non-fit.** Explicit "Summer 2026 only" or similar.

## Decision
Filter chain assigns each posting a `start_date_confidence` of `match`, `unknown`, or `non-fit`. Only `non-fit` is dropped (when `filters.drop_summer_2026: true` in config). `unknown` is kept and surfaced in the brief with a "Start date unclear" flag.

The display always includes the matched phrase verbatim (e.g. "start date language: 'Fall 2026'") so the user can verify.

## Consequences
Easier: catches every legitimate posting; user can triage the unknowns with eyes.
Harder: brief has more postings than a strict filter would produce, so scoring has to do more work to keep the top tier clean.

## Alternatives considered
- **Drop all unknowns.** Rejected: throws away most of the corpus.
- **Drop unknowns only if the role is at a company known to run a single summer-only intern program.** Considered, deferred — would need a company allowlist/denylist, which is its own maintenance burden.
- **Use an LLM to extract start dates from body text.** Possible future iteration — would need a budget for inference and a strong prompt. Out of scope for v1.
