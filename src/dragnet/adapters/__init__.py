"""Adapter registry. Adds adapters by importing them and listing in `ALL`."""

from __future__ import annotations

from dragnet.adapters.adzuna import AdzunaAdapter
from dragnet.adapters.arbeitnow import ArbeitnowAdapter
from dragnet.adapters.base import Adapter
from dragnet.adapters.hn_hiring import HNHiringAdapter
from dragnet.adapters.jsearch import JSearchAdapter
from dragnet.adapters.remoteok import RemoteOKAdapter
from dragnet.adapters.remotive import RemotiveAdapter
from dragnet.adapters.themuse import TheMuseAdapter
from dragnet.adapters.usajobs import USAJobsAdapter

# name -> class. The config's `sources` dict toggles by name.
REGISTRY: dict[str, type[Adapter]] = {
    "usajobs": USAJobsAdapter,
    "adzuna": AdzunaAdapter,
    "jsearch": JSearchAdapter,
    "remotive": RemotiveAdapter,
    "arbeitnow": ArbeitnowAdapter,
    "remoteok": RemoteOKAdapter,
    "hn_hiring": HNHiringAdapter,
    "themuse": TheMuseAdapter,
}

__all__ = ["Adapter", "REGISTRY"]
