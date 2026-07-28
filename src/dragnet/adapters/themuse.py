"""The Muse adapter. https://www.themuse.com/developers/api/v2

Public JSON API, no key required (500 req/hr unauthenticated). The Muse exposes
a structured `level=Internship` filter but no free-text keyword param, so we pull
Internship-level pages and let the pipeline keyword/category-match — same
client-side screen the other no-auth adapters use.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx

from dragnet.adapters.base import Adapter
from dragnet.models import AdapterQuery, Posting

log = logging.getLogger(__name__)

BASE_URL = "https://www.themuse.com/api/public/jobs"


class TheMuseAdapter(Adapter):
    name = "themuse"

    async def search(self, query: AdapterQuery) -> list[Posting]:
        postings: list[Posting] = []
        kw_lower = [k.lower() for k in query.keywords]
        for page in range(1, self.cfg.adapters.themuse_pages + 1):
            params: dict[str, Any] = {
                "page": page,
                "level": "Internship",
                "descending": "true",  # newest first
            }
            if query.location_hint:
                params["location"] = query.location_hint
            try:
                r = await self.client.get(
                    BASE_URL,
                    params=params,
                    timeout=self.cfg.adapters.per_adapter_timeout_sec,
                )
                r.raise_for_status()
                data = r.json()
            except (httpx.HTTPError, ValueError) as e:
                self._log_result(0, f"page={page} {type(e).__name__}: {e}")
                break

            results = data.get("results", []) or []
            for item in results:
                try:
                    title = (item.get("name") or "").lower()
                    desc = (item.get("contents") or "").lower()
                    # Client-side keyword screen: at least one keyword must hit.
                    if kw_lower and not any(k in title or k in desc for k in kw_lower):
                        continue
                    postings.append(self._normalize(item))
                except (KeyError, TypeError, ValueError) as e:
                    log.debug("themuse normalize skip: %s", e)

            if not results or page >= data.get("page_count", page):
                break

        self._log_result(len(postings))
        return postings

    def _normalize(self, item: dict[str, Any]) -> Posting:
        posted_at = None
        if item.get("publication_date"):
            try:
                posted_at = datetime.fromisoformat(item["publication_date"].replace("Z", "+00:00"))
            except ValueError:
                posted_at = None

        company = (item.get("company") or {}).get("name", "")
        locs = [loc.get("name", "") for loc in (item.get("locations") or []) if loc.get("name")]
        location = "; ".join(locs) or "—"

        return Posting(
            source=self.name,
            source_id=str(item.get("id", "")),
            url=(item.get("refs") or {}).get("landing_page", ""),
            title=item.get("name", ""),
            company=company,
            location=location,
            description=item.get("contents", ""),
            posted_at=posted_at,
            raw=item,
        )
