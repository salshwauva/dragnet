"""Data models. The Posting is the lingua franca across adapters, pipeline, and notifiers."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AdapterQuery(BaseModel):
    """What an adapter is asked to search for. Adapters translate this into their native syntax."""

    keywords: list[str] = Field(default_factory=list)
    location_hint: str | None = None
    intern_only: bool = True
    earliest_start: date | None = None


class Posting(BaseModel):
    """One job posting, normalized across all sources."""

    model_config = ConfigDict(extra="ignore")

    # source identity
    source: str  # adapter name, e.g. "usajobs"
    source_id: str  # source's native ID; component of fingerprint
    url: str

    # surface
    title: str
    company: str
    location: str  # raw location string from the source

    # body
    description: str = ""  # full or partial body; can be empty

    # dates
    posted_at: datetime | None = None
    start_date_raw: str | None = None  # raw start date language extracted from body

    # flags (computed by filter chain)
    is_remote: bool = False
    is_hybrid: bool = False
    requires_citizenship: bool = False
    requires_clearance: bool = False
    intern_signal: float = 0.0  # 0.0-1.0; >= 0.5 means we believe it's intern-friendly
    start_date_confidence: str = "unknown"  # "match" | "unknown" | "non-fit"

    # derived
    matched_categories: list[str] = Field(default_factory=list)
    score: float = 0.0
    fingerprint: str = ""

    # debugging
    raw: dict[str, Any] = Field(default_factory=dict)

    def signals_summary(self) -> str:
        """One-line human-readable summary of the flags. For markdown brief output."""
        bits = []
        if self.is_remote:
            bits.append("Remote")
        elif self.is_hybrid:
            bits.append("Hybrid")
        if self.requires_clearance:
            bits.append("Clearance")
        elif self.requires_citizenship:
            bits.append("US Citizen")
        if self.start_date_confidence == "match":
            bits.append("Fall-2026 fit")
        elif self.start_date_confidence == "unknown":
            bits.append("Start date unclear")
        return " · ".join(bits) if bits else "—"
