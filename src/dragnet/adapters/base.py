"""Adapter base class. Each source subclasses this."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import httpx

from dragnet.config import Config
from dragnet.models import AdapterQuery, Posting

log = logging.getLogger(__name__)


class Adapter(ABC):
    """One adapter per source. Owns network calls and normalization.

    Adapters are async because the orchestrator fans them out concurrently.
    Each subclass must define `name` (matches the config key) and implement
    `search`. Adapters do NOT filter or score; they fetch and normalize.
    """

    name: str = ""

    def __init__(self, cfg: Config, client: httpx.AsyncClient) -> None:
        self.cfg = cfg
        self.client = client

    @abstractmethod
    async def search(self, query: AdapterQuery) -> list[Posting]:
        """Fetch postings matching the query. Return normalized Posting list.

        Implementations should:
        - Translate `query.keywords` into the source's native search syntax
          (OR-joined where the API supports it; otherwise issue multiple calls).
        - Apply only API-level filters (e.g. country=us, posting_type=internship)
          that the source natively supports. All other filtering lives in the pipeline.
        - Return Postings with `source` set to `self.name` and `source_id`
          set to the source's native ID.
        - Be resilient to 429 / 5xx: log + return empty list, do not raise.
        """

    def _log_result(self, count: int, error: str | None = None) -> None:
        """Helper for adapters to report status. Adapters should call this."""
        if error:
            log.warning("adapter=%s status=error msg=%s", self.name, error)
        else:
            log.info("adapter=%s status=ok count=%d", self.name, count)
