"""Arbeitnow adapter. https://www.arbeitnow.com/api/job-board-api

Tech jobs. Originally EU-centric but has US postings. No auth, no quota.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx

from dragnet.adapters.base import Adapter
from dragnet.models import AdapterQuery, Posting

log = logging.getLogger(__name__)

BASE_URL = "https://www.arbeitnow.com/api/job-board-api"


class ArbeitnowAdapter(Adapter):
    name = "arbeitnow"

    async def search(self, query: AdapterQuery) -> list[Posting]:
        try:
            r = await self.client.get(
                BASE_URL,
                timeout=self.cfg.adapters.per_adapter_timeout_sec,
            )
            r.raise_for_status()
            data = r.json()
        except (httpx.HTTPError, ValueError) as e:
            self._log_result(0, f"{type(e).__name__}: {e}")
            return []

        jobs = data.get("data", []) or []
        postings: list[Posting] = []
        kw_lower = [k.lower() for k in query.keywords]
        for item in jobs:
            try:
                title = (item.get("title") or "").lower()
                desc = (item.get("description") or "").lower()
                if kw_lower and not any(k in title or k in desc for k in kw_lower):
                    continue
                postings.append(self._normalize(item))
            except (KeyError, TypeError, ValueError) as e:
                log.debug("arbeitnow normalize skip: %s", e)

        self._log_result(len(postings))
        return postings

    def _normalize(self, item: dict[str, Any]) -> Posting:
        posted_at = None
        ts = item.get("created_at")
        if isinstance(ts, (int, float)):
            posted_at = datetime.fromtimestamp(ts)
        tags = item.get("tags", []) or []
        is_remote = bool(item.get("remote")) or "remote" in [t.lower() for t in tags]
        return Posting(
            source=self.name,
            source_id=item.get("slug", ""),
            url=item.get("url", ""),
            title=item.get("title", ""),
            company=item.get("company_name", ""),
            location=item.get("location", "") or "",
            description=item.get("description", ""),
            posted_at=posted_at,
            is_remote=is_remote,
            raw=item,
        )
