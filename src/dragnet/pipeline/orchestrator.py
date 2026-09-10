"""Orchestrator: fans adapters out concurrently, collects results."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

import httpx

from dragnet.adapters import REGISTRY
from dragnet.config import Config
from dragnet.models import AdapterQuery, Posting

log = logging.getLogger(__name__)


@dataclass
class FetchResult:
    postings: list[Posting] = field(default_factory=list)
    # Sources whose search returned without raising. Only these count as a
    # "successful crawl" for lifecycle absence tracking.
    succeeded: set[str] = field(default_factory=set)
    failed: set[str] = field(default_factory=set)


async def fetch_all(cfg: Config, query: AdapterQuery) -> FetchResult:
    """Run every enabled adapter against `query` concurrently. Return merged result."""
    enabled = [name for name, on in cfg.sources.items() if on and name in REGISTRY]
    result = FetchResult()
    if not enabled:
        log.warning("no adapters enabled in config.sources")
        return result

    sem = asyncio.Semaphore(cfg.adapters.concurrent_limit)
    async with httpx.AsyncClient() as client:

        async def run(name: str) -> list[Posting]:
            adapter = REGISTRY[name](cfg, client)
            async with sem:
                try:
                    batch = await adapter.search(query)
                except Exception as e:  # noqa: BLE001 — adapter errors shouldn't kill the run
                    log.warning("adapter=%s crashed: %s", name, e)
                    result.failed.add(name)
                    return []
                result.succeeded.add(name)
                return batch

        results = await asyncio.gather(*(run(n) for n in enabled))

    for batch in results:
        result.postings.extend(batch)
    log.info(
        "orchestrator: %d/%d adapters ok, %d total postings",
        len(result.succeeded),
        len(enabled),
        len(result.postings),
    )
    return result
