"""HN 'Who is Hiring' adapter. https://hn.algolia.com/api

Hits the Algolia HN search to find the latest 'Ask HN: Who is hiring?' thread,
then fetches its top-level comments and treats each as a posting.

The thread is monthly. Each comment is one company's pitch. We extract the
first line as title-ish text and the rest as description. The 'company' is
the first capitalized phrase, best-effort.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any

import httpx

from dragnet.adapters.base import Adapter
from dragnet.models import AdapterQuery, Posting

log = logging.getLogger(__name__)

# search_by_date sorts newest-first. The plain /search endpoint ranks by
# relevance and can return a years-old thread, so always use the dated one.
SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date"
ITEM_URL = "https://hn.algolia.com/api/v1/items/{item_id}"


class HNHiringAdapter(Adapter):
    name = "hn_hiring"

    async def search(self, query: AdapterQuery) -> list[Posting]:
        # 1. Find the latest "Ask HN: Who is hiring?" thread.
        try:
            r = await self.client.get(
                SEARCH_URL,
                params={
                    "query": "Ask HN: Who is hiring?",
                    "tags": "story,author_whoishiring",
                    "hitsPerPage": "5",
                },
                timeout=self.cfg.adapters.per_adapter_timeout_sec,
            )
            r.raise_for_status()
            hits = r.json().get("hits", [])
        except (httpx.HTTPError, ValueError) as e:
            self._log_result(0, f"search {type(e).__name__}: {e}")
            return []
        # The whoishiring account also posts "Who wants to be hired?" and
        # "freelancer?" threads; pick the newest one that is actually hiring.
        story = next(
            (h for h in hits if "who is hiring" in (h.get("title") or "").lower()),
            None,
        )
        if story is None:
            self._log_result(0, "no 'Who is hiring?' thread found")
            return []
        story_id = story["objectID"]

        # 2. Fetch the thread (returns the story + nested comments).
        try:
            r = await self.client.get(
                ITEM_URL.format(item_id=story_id),
                timeout=self.cfg.adapters.per_adapter_timeout_sec,
            )
            r.raise_for_status()
            thread = r.json()
        except (httpx.HTTPError, ValueError) as e:
            self._log_result(0, f"thread {type(e).__name__}: {e}")
            return []

        top_level = thread.get("children", []) or []
        kw_lower = [k.lower() for k in query.keywords]
        postings: list[Posting] = []
        for c in top_level:
            text = c.get("text") or ""
            if not text:
                continue
            text_lower = text.lower()
            # Must mention intern + at least one keyword (intern is the wider filter,
            # categories provide the signal).
            if "intern" not in text_lower:
                continue
            if kw_lower and not any(k in text_lower for k in kw_lower):
                continue
            try:
                postings.append(self._normalize(c, story_id))
            except (KeyError, TypeError, ValueError) as e:
                log.debug("hn normalize skip: %s", e)

        self._log_result(len(postings))
        return postings

    def _normalize(self, comment: dict[str, Any], story_id: str) -> Posting:
        text = comment.get("text", "")
        # First line is usually "CompanyName | Role | Location | Type"
        first_line = re.sub(r"<[^>]+>", "", text).split("\n")[0]
        first_line = first_line[:200]
        company_guess = first_line.split("|")[0].strip() if "|" in first_line else first_line
        comment_id = comment.get("id", "")
        url = f"https://news.ycombinator.com/item?id={comment_id}"

        posted_at = None
        ts = comment.get("created_at_i")
        if isinstance(ts, (int, float)):
            posted_at = datetime.fromtimestamp(ts)
        return Posting(
            source=self.name,
            source_id=f"{story_id}:{comment_id}",
            url=url,
            title=first_line or "(HN Who is Hiring)",
            company=company_guess[:80] or "(unknown)",
            location="(see post)",
            description=re.sub(r"<[^>]+>", "", text),
            posted_at=posted_at,
            raw=comment,
        )
