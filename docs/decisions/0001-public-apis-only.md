# ADR 0001: Use only public JSON APIs; no HTML scraping

## Status
Accepted — 2026-05-22

## Context
The genre of "developer job aggregator" is full of projects that scrape LinkedIn / Indeed / Glassdoor HTML. Those projects break on a 6-12 month cadence because the target sites change markup. They also tend to get IP-banned. Dragnet needs to run reliably on a personal laptop for at least a year without me babysitting adapters.

## Decision
All adapters consume public JSON APIs only. The seven sources we chose all have either no-auth or free-tier-keyed JSON endpoints: USAJobs, Adzuna, JSearch (RapidAPI aggregator), Remotive, Arbeitnow, RemoteOK, and HN's Algolia index.

For coverage gaps (LinkedIn especially), we route through aggregators like JSearch on RapidAPI rather than scraping ourselves. The aggregator absorbs the scraping risk.

## Consequences
Easier: stable adapters, no IP-ban risk, no headless browser dependency.
Harder: some sources require keys we have to register for; JSearch has a monthly quota; coverage isn't 100% (Wellfound, YC, Built In require Layer 1 native alerts).

## Alternatives considered
- **JobSpy library or similar HTML scrapers.** Rejected: maintenance burden, breakage cadence.
- **Headless-browser scraping (Playwright).** Rejected: overkill and slow for the volume we need.
- **Building one adapter per company (Workday/Greenhouse/Lever).** Considered for a future iteration. Each individual company's careers page often exposes a Workday/Greenhouse JSON endpoint. Out of scope for v1.
