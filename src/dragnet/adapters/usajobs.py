"""USAJobs adapter. https://developer.usajobs.gov/

Federal jobs board, government-mandated, very stable API. Best signal for
cleared/citizenship-required roles, which line up with Sophia's eligibility edge.

Auth: User-Agent must be the registered email; Authorization-Key header carries the API key.
Rate limits: documented as "be reasonable" — no published quota. Page size up to 500.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx

from dragnet.adapters.base import Adapter
from dragnet.models import AdapterQuery, Posting

log = logging.getLogger(__name__)

BASE_URL = "https://data.usajobs.gov/api/Search"


class USAJobsAdapter(Adapter):
    name = "usajobs"

    async def search(self, query: AdapterQuery) -> list[Posting]:
        secrets = self.cfg.secrets
        if not secrets.usajobs_auth_key or not secrets.usajobs_user_agent_email:
            self._log_result(0, "missing USAJOBS_AUTH_KEY or USAJOBS_USER_AGENT_EMAIL")
            return []

        headers = {
            "User-Agent": secrets.usajobs_user_agent_email,
            "Authorization-Key": secrets.usajobs_auth_key,
            "Host": "data.usajobs.gov",
        }
        # USAJobs supports OR via comma-separated Keyword values.
        keyword_str = ",".join(query.keywords) if query.keywords else "intern"
        params: dict[str, Any] = {
            "Keyword": keyword_str,
            "ResultsPerPage": self.cfg.adapters.usajobs_page_size,
            # USAJobs uses PositionScheduleTypeCode but that's full/part time, not intern.
            # Intern detection lives in pipeline/filters. Here we cast a wide net.
        }
        if query.location_hint:
            params["LocationName"] = query.location_hint

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
            self._log_result(0, f"{type(e).__name__}: {e}")
            return []

        items = data.get("SearchResult", {}).get("SearchResultItems", [])
        postings: list[Posting] = []
        for item in items:
            try:
                postings.append(self._normalize(item))
            except (KeyError, TypeError, ValueError) as e:
                log.debug("usajobs normalize skip: %s", e)
                continue

        self._log_result(len(postings))
        return postings

    def _normalize(self, item: dict[str, Any]) -> Posting:
        descriptor = item["MatchedObjectDescriptor"]
        position_id = descriptor.get("PositionID", item.get("MatchedObjectId", ""))
        title = descriptor.get("PositionTitle", "")
        org = descriptor.get("OrganizationName") or descriptor.get("DepartmentName", "")
        url = descriptor.get("PositionURI", "")

        locations = descriptor.get("PositionLocation", []) or []
        loc_strs = [loc.get("LocationName", "") for loc in locations if loc.get("LocationName")]
        location = "; ".join(loc_strs) or "Remote (US)"

        # USAJobs has a structured user-area "Details" object with a description.
        user_area = descriptor.get("UserArea", {}).get("Details", {})
        summary = descriptor.get("QualificationSummary") or ""
        major_duties = user_area.get("MajorDuties", "") or ""
        description = (summary + "\n\n" + major_duties).strip()

        # Posting date.
        posted_at = None
        date_str = descriptor.get("PublicationStartDate", "")
        if date_str:
            try:
                posted_at = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except ValueError:
                posted_at = None

        # USAJobs always requires citizenship for nearly all postings; flag it.
        requires_citizenship = True
        # Clearance signal can come from many fields; check description.
        text_for_clearance = (description + " " + title).lower()
        requires_clearance = any(
            kw in text_for_clearance
            for kw in (
                "security clearance",
                "secret clearance",
                "top secret",
                "ts/sci",
                "polygraph",
                "active clearance",
            )
        )

        return Posting(
            source=self.name,
            source_id=str(position_id),
            url=url,
            title=title,
            company=org,
            location=location,
            description=description,
            posted_at=posted_at,
            requires_citizenship=requires_citizenship,
            requires_clearance=requires_clearance,
            raw=item,
        )
