# ADR 0002: Adapter pattern with async fan-out via httpx.AsyncClient

## Status
Accepted — 2026-05-22

## Context
Seven sources with different auth schemes, response shapes, and rate-limit behaviors. Sequential HTTP across all seven would take 30-60 seconds per run. We want a clean place to add an eighth source without touching the pipeline or notifiers.

## Decision
One `Adapter` ABC under `src/dragnet/adapters/base.py`. Each source is one subclass that implements `async def search(query) -> list[Posting]`. The orchestrator in `pipeline/orchestrator.py` fans them out concurrently via `asyncio.gather`, bounded by a semaphore (`adapters.concurrent_limit`). All adapters share one `httpx.AsyncClient`.

Adapters do NOT filter or score. They fetch and normalize. Everything else is the pipeline's job.

## Consequences
Easier: parallel fetches, contained per-adapter complexity, trivial to add a new source.
Harder: async debugging when adapters misbehave. Per-adapter timeouts must be explicit.

## Alternatives considered
- **Threads with `concurrent.futures.ThreadPoolExecutor`.** Workable but the rest of Python is moving to async; this is a good place to stay consistent.
- **One module that handles everything, no ABC.** Rejected: would tangle source-specific quirks (USAJobs's header auth vs Adzuna's query-param auth vs RapidAPI's host+key headers) into one mess.
