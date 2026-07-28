"""Orchestrator: fans adapters out concurrently, collects results."""

from __future__ import annotations

import asyncio
import logging

import httpx

from dragnet.adapters import REGISTRY
from dragnet.config import Config
from dragnet.models import AdapterQuery, Posting

log = logging.getLogger(__name__)


async def fetch_all(cfg: Config, query: AdapterQuery) -> list[Posting]:
    """Run every enabled adapter against `query` concurrently. Return merged list."""
    enabled = [name for name, on in cfg.sources.items() if on and name in REGISTRY]
    if not enabled:
        log.warning("no adapters enabled in config.sources")
        return []

    sem = asyncio.Semaphore(cfg.adapters.concurrent_limit)
    async with httpx.AsyncClient() as client:

        async def run(name: str) -> list[Posting]:
            adapter = REGISTRY[name](cfg, client)
            async with sem:
                try:
                    return await adapter.search(query)
                except Exception as e:  # noqa: BLE001 — adapter errors shouldn't kill the run
                    log.warning("adapter=%s crashed: %s", name, e)
                    return []

        results = await asyncio.gather(*(run(n) for n in enabled))

    merged: list[Posting] = []
    for batch in results:
        merged.extend(batch)
    log.info("orchestrator: %d adapters returned %d total postings", len(enabled), len(merged))
    return merged
