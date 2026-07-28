"""RemoteOK adapter. https://remoteok.com/api

Remote tech jobs. Public JSON feed (first element is a legal notice, skip it).
Sets a custom User-Agent because the default httpx UA gets rate-limited.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx

from dragnet.adapters.base import Adapter
from dragnet.models import AdapterQuery, Posting

log = logging.getLogger(__name__)

BASE_URL = "https://remoteok.com/api"


class RemoteOKAdapter(Adapter):
    name = "remoteok"

    async def search(self, query: AdapterQuery) -> list[Posting]:
        headers = {"User-Agent": "dragnet/0.1 (personal-tool)"}
        try:
            r = await self.client.get(
                BASE_URL,
                headers=headers,
                timeout=self.cfg.adapters.per_adapter_timeout_sec,
            )
            r.raise_for_status()
            data = r.json()
        except (httpx.HTTPError, ValueError) as e:
            self._log_result(0, f"{type(e).__name__}: {e}")
            return []

        # First element is a legal/meta object — skip it.
        if isinstance(data, list) and data and "id" not in data[0]:
            data = data[1:]

        postings: list[Posting] = []
        kw_lower = [k.lower() for k in query.keywords]
        for item in data:
            try:
                if not isinstance(item, dict):
                    continue
                title = (item.get("position") or item.get("title") or "").lower()
                desc = (item.get("description") or "").lower()
                if kw_lower and not any(k in title or k in desc for k in kw_lower):
                    continue
                postings.append(self._normalize(item))
            except (KeyError, TypeError, ValueError) as e:
                log.debug("remoteok normalize skip: %s", e)

        self._log_result(len(postings))
        return postings

    def _normalize(self, item: dict[str, Any]) -> Posting:
        posted_at = None
        date_str = item.get("date") or ""
        if date_str:
            try:
                posted_at = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except ValueError:
                posted_at = None
        return Posting(
            source=self.name,
            source_id=str(item.get("id", "")),
            url=item.get("url") or item.get("apply_url", ""),
            title=item.get("position") or item.get("title", ""),
            company=item.get("company", ""),
            location=item.get("location", "Remote"),
            description=item.get("description", ""),
            posted_at=posted_at,
            is_remote=True,
            raw=item,
        )
