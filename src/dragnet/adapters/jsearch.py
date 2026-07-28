"""JSearch adapter. https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch

Aggregates LinkedIn, Indeed, Glassdoor, ZipRecruiter via a single RapidAPI endpoint.
Free tier: 200 calls/month. Watch the quota — `jsearch_pages` config knob controls
how many calls per run.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx

from dragnet.adapters.base import Adapter
from dragnet.models import AdapterQuery, Posting

log = logging.getLogger(__name__)

BASE_URL = "https://jsearch.p.rapidapi.com/search"


class JSearchAdapter(Adapter):
    name = "jsearch"

    async def search(self, query: AdapterQuery) -> list[Posting]:
        secrets = self.cfg.secrets
        if not secrets.rapidapi_key:
            self._log_result(0, "missing RAPIDAPI_KEY")
            return []

        headers = {
            "x-rapidapi-key": secrets.rapidapi_key,
            "x-rapidapi-host": "jsearch.p.rapidapi.com",
        }
        # JSearch wants a single search string. OR is implicit on space-separation.
        q_terms = list(query.keywords) + ["intern"]
        q = " ".join(q_terms)
        if query.location_hint:
            q = f"{q} in {query.location_hint}"

        postings: list[Posting] = []
        for page in range(1, self.cfg.adapters.jsearch_pages + 1):
            params: dict[str, Any] = {
                "query": q,
                "page": str(page),
                "num_pages": "1",
                "employment_types": "INTERN",
                "country": "us",
                "date_posted": "month",
            }
            try:
                r = await self.client.get(
                    BASE_URL,
                    headers=headers,
                    params=params,
                    timeout=self.cfg.adapters.per_adapter_timeout_sec,
                )
                r.raise_for_status()
                data = r.json()
            except (httpx.HTTPError, ValueError) as e:
                self._log_result(0, f"page={page} {type(e).__name__}: {e}")
                break

            results = data.get("data", []) or []
            for item in results:
                try:
                    postings.append(self._normalize(item))
                except (KeyError, TypeError, ValueError) as e:
                    log.debug("jsearch normalize skip: %s", e)
            if not results:
                break

        self._log_result(len(postings))
        return postings

    def _normalize(self, item: dict[str, Any]) -> Posting:
        posted_at = None
        ts = item.get("job_posted_at_timestamp")
        if isinstance(ts, (int, float)):
            posted_at = datetime.fromtimestamp(ts)

        city = item.get("job_city") or ""
        state = item.get("job_state") or ""
        country = item.get("job_country") or ""
        loc_parts = [p for p in (city, state, country) if p]
        location = ", ".join(loc_parts) if loc_parts else "—"
        is_remote = bool(item.get("job_is_remote"))

        return Posting(
            source=self.name,
            source_id=str(item.get("job_id", "")),
            url=item.get("job_apply_link") or item.get("job_google_link", ""),
            title=item.get("job_title", ""),
            company=item.get("employer_name", ""),
            location=location,
            description=item.get("job_description", ""),
            posted_at=posted_at,
            is_remote=is_remote,
            raw=item,
        )
