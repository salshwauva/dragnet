"""Adzuna adapter. https://developer.adzuna.com/

US job aggregator with keyword search. 1000 calls/month on the free tier.
Each call returns up to 50 results.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx

from dragnet.adapters.base import Adapter
from dragnet.models import AdapterQuery, Posting

log = logging.getLogger(__name__)

BASE_URL = "https://api.adzuna.com/v1/api/jobs/us/search/{page}"


class AdzunaAdapter(Adapter):
    name = "adzuna"

    async def search(self, query: AdapterQuery) -> list[Posting]:
        secrets = self.cfg.secrets
        if not secrets.adzuna_app_id or not secrets.adzuna_app_key:
            self._log_result(0, "missing ADZUNA_APP_ID or ADZUNA_APP_KEY")
            return []

        # Adzuna treats `what` as AND across terms, so joining every category
        # keyword into one `what` returns almost nothing. Use `what_or` for the
        # OR-of-keywords, and require "intern" via `what` (Adzuna lacks a
        # structured intern filter). The pipeline category-matches afterward.
        what_or = " ".join(query.keywords)

        postings: list[Posting] = []
        for page in range(1, self.cfg.adapters.adzuna_pages + 1):
            params: dict[str, Any] = {
                "app_id": secrets.adzuna_app_id,
                "app_key": secrets.adzuna_app_key,
                "results_per_page": 50,
                "what": "intern",
                "content-type": "application/json",
            }
            if what_or:
                params["what_or"] = what_or
            if query.location_hint:
                params["where"] = query.location_hint
            try:
                r = await self.client.get(
                    BASE_URL.format(page=page),
                    params=params,
                    timeout=self.cfg.adapters.per_adapter_timeout_sec,
                )
                r.raise_for_status()
                data = r.json()
            except (httpx.HTTPError, ValueError) as e:
                self._log_result(0, f"page={page} {type(e).__name__}: {e}")
                break
            results = data.get("results", [])
            for item in results:
                try:
                    postings.append(self._normalize(item))
                except (KeyError, TypeError, ValueError) as e:
                    log.debug("adzuna normalize skip: %s", e)
            if not results:
                break

        self._log_result(len(postings))
        return postings

    def _normalize(self, item: dict[str, Any]) -> Posting:
        posted_at = None
        if item.get("created"):
            try:
                posted_at = datetime.fromisoformat(item["created"].replace("Z", "+00:00"))
            except ValueError:
                posted_at = None
        loc = item.get("location", {})
        location = loc.get("display_name", "") if isinstance(loc, dict) else str(loc or "")
        company = (
            (item.get("company") or {}).get("display_name", "")
            if isinstance(item.get("company"), dict)
            else str(item.get("company", ""))
        )

        return Posting(
            source=self.name,
            source_id=str(item.get("id", "")),
            url=item.get("redirect_url", ""),
            title=item.get("title", ""),
            company=company,
            location=location,
            description=item.get("description", ""),
            posted_at=posted_at,
            raw=item,
        )
