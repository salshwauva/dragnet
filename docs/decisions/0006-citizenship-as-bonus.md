# ADR 0006: Citizenship/clearance as scoring bonus, never a filter

## Status
Accepted — 2026-05-22

## Context
Sophia is a US citizen, which means citizenship-required and clearance-eligible postings are open to her where they'd be hard barriers for many candidates. That smaller talent pool is an edge. But she's also open to roles that don't require either — they're the majority of internships.

Naively, we could filter to "citizenship-required OR clearance-eligible only" to surface only her edge cases, but that throws away the bulk of viable roles.

## Decision
Treat citizenship-required and clearance-eligible as **scoring bonuses**, never as filters. A posting that requires citizenship gets `+citizenship_bonus` (default 20). A posting that mentions clearance gets `+clearance_bonus` (default 30). Both stack.

The effect: cleared roles bubble up in the brief without crowding out non-cleared roles she's equally qualified for. Top-tier output mixes both, weighted toward roles where her eligibility is rare.

## Consequences
Easier: full corpus retained; rare-edge roles get visible without exclusivity.
Harder: scoring weights need tuning during Phase 2 — if cleared roles dominate too aggressively, lower `clearance_bonus`.

## Alternatives considered
- **Filter to cleared-only.** Rejected: throws away 80%+ of viable internships.
- **Filter out cleared roles, ignore the edge.** Rejected: wastes her actual advantage.
- **Run cleared roles in a separate brief.** Considered, deferred. If the unified brief turns out to be too noisy, this is the right escalation. Document the trigger condition before splitting.
