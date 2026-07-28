"""Remotive adapter. https://remotive.com/api/remote-jobs

Remote-only tech jobs. No auth, no quota. Returns up to ~200 jobs in one call.
We filter client-side for keyword + intern (Remotive lacks structured intern filter).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx

from dragnet.adapters.base import Adapter
from dragnet.models import AdapterQuery, Posting

log = logging.getLogger(__name__)

BASE_URL = "https://remotive.com/api/remote-jobs"


class RemotiveAdapter(Adapter):
    name = "remotive"

    async def search(self, query: AdapterQuery) -> list[Posting]:
        params: dict[str, Any] = {"limit": 200, "category": "software-dev"}
        try:
            r = await self.client.get(
                BASE_URL,
                params=params,
                timeout=self.cfg.adapters.per_adapter_timeout_sec,
            )
            r.raise_for_status()
            data = r.json()
        except (httpx.HTTPError, ValueError) as e:
            self._log_result(0, f"{type(e).__name__}: {e}")
            return []

        jobs = data.get("jobs", [])
        postings: list[Posting] = []
        kw_lower = [k.lower() for k in query.keywords]
        for item in jobs:
            try:
                title = (item.get("title") or "").lower()
                desc = (item.get("description") or "").lower()
                # Client-side keyword screen: at least one keyword must hit somewhere.
                if kw_lower and not any(k in title or k in desc for k in kw_lower):
                    continue
                postings.append(self._normalize(item))
            except (KeyError, TypeError, ValueError) as e:
                log.debug("remotive normalize skip: %s", e)

        self._log_result(len(postings))
        return postings

    def _normalize(self, item: dict[str, Any]) -> Posting:
        posted_at = None
        if item.get("publication_date"):
            try:
                posted_at = datetime.fromisoformat(item["publication_date"].replace("Z", "+00:00"))
            except ValueError:
                posted_at = None
        return Posting(
            source=self.name,
            source_id=str(item.get("id", "")),
            url=item.get("url", ""),
            title=item.get("title", ""),
            company=item.get("company_name", ""),
            location=item.get("candidate_required_location", "Remote"),
            description=item.get("description", ""),
            posted_at=posted_at,
            is_remote=True,
            raw=item,
        )
