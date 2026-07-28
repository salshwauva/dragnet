# Layer 1 — Native alerts setup

Dragnet (Layer 2) sweeps seven public APIs every 12 hours. It does NOT cover:
- LinkedIn (no public API; JSearch on RapidAPI catches some but not all)
- Handshake (Penn's career portal — university-gated)
- ClearanceJobs / ClearedJobs.net (cleared roles aggregator)
- Built In (Boston/NYC/Chicago tech scene)
- Wellfound (formerly AngelList — startups)
- YC Work at a Startup (YC portfolio)
- Otta / Welcome to the Jungle (curated)
- Direct Workday portals for the defense primes (Lockheed, Northrop, Raytheon, etc.)

For these, set up **native saved-search alerts** that email you directly. Then route the emails to `Jobs/Alerts/*` labels (see `GMAIL_FILTERS.md`).

**Time budget:** ~60 minutes for the full list. ~25 minutes if you only do the top 5 (marked ⭐).

---

## ⭐ 1. USAJobs (saved searches + email alerts)

Even though Dragnet hits the USAJobs API, the native alert system catches postings that hit between Dragnet's 12-hour runs.

1. Go to https://www.usajobs.gov/ and sign in (create account if needed).
2. Top right → **My Account** → **Saved Searches**.
3. Create one saved search per category:

   **Search A — Software / Engineering Intern**
   - Keywords: `software intern OR software engineer intern OR pathways software`
   - Location: leave blank (covers everywhere)
   - **Save** → name it `dragnet-swe`, notification frequency: **Daily**.

   **Search B — Cleared / Cybersecurity Intern**
   - Keywords: `cybersecurity intern OR information security intern OR cleared intern`
   - **Save** → `dragnet-cleared`, frequency: **Daily**.

   **Search C — Computational Biology / Bioinformatics Intern**
   - Keywords: `bioinformatics OR computational biology OR data science health`
   - Filter: Internship-Pathways
   - **Save** → `dragnet-biotech`, frequency: **Daily**.

4. Verify the first alert arrives at the email tied to your USAJobs account.

---

## ⭐ 2. LinkedIn Job Alerts

LinkedIn's saved searches turn into email alerts.

1. Go to https://www.linkedin.com/jobs/ → search bar.
2. Run each search below, then click **Set alert** on the results page.

   **Search A:** `software engineering intern` · Filter: **Job type: Internship**, **Date posted: Past week**.
   **Search B:** `embedded software intern OR firmware intern OR rtos`
   **Search C:** `machine learning intern OR ML intern OR applied ML`
   **Search D:** `cleared intern OR security clearance intern`
   **Search E:** `bioinformatics intern OR computational biology intern`
   **Search F:** Location: `Boston, MA` · keyword: `software intern` (catches anything Boston-tagged).
   **Search G:** Location: `Washington, DC metro area` · keyword: `software intern OR cleared`

3. For each: alert frequency: **Daily**.
4. Filter all to your `Jobs/Alerts/LinkedIn` label (per `GMAIL_FILTERS.md`).

---

## ⭐ 3. Handshake (Penn)

Handshake is Penn's career portal. The Penn talent pool catches things outside aggregators.

1. Go to https://app.joinhandshake.com/ → sign in with your Penn SSO.
2. Use **Jobs** → search bar.
3. Run each search and click **Save search**:
   - `software engineering intern` (Job Type: Internship)
   - `embedded firmware intern`
   - `machine learning intern`
   - `cleared intern` (this catches DoD-adjacent postings)
4. **Notification settings**: top right → **Settings** → **Notifications** → enable **Daily digest** for saved searches.

Note: Penn often has direct-to-company internship pipelines that only appear here. This is the most under-rated source on this list.

---

## ⭐ 4. ClearanceJobs

The cleared-role marketplace. Your citizenship + clearance-eligibility makes this a high-signal source.

1. Go to https://www.clearancejobs.com/ and create a free job seeker account.
2. **Search** → keyword: `intern OR co-op OR pathways`.
3. Filter: **Job Type → Internship**.
4. Click **Save Search** → name it `dragnet-cleared-intern`.
5. **Account → Email Preferences** → enable **Daily Job Match Email**.

---

## ⭐ 5. ClearedJobs.net

The other cleared-roles board. Smaller volume but different employer base than ClearanceJobs.

1. Go to https://clearedjobs.net/ → create job seeker account.
2. **Search Jobs** → keyword: `intern OR internship`.
3. **Save Search** with email alerts: **Daily**.

---

## 6. Built In

Built In runs city-specific tech job sites (Boston, NYC, Chicago, etc).

1. Built In Boston: https://www.builtinboston.com/ → create account.
2. Set up alerts:
   - **Boston:** keyword `software engineer intern OR ML intern`, alert: **Daily**.
   - **NYC** (https://www.builtinnyc.com/): same searches.
   - **Chicago** (https://www.builtinchicago.org/): same searches if you want broader coverage.
3. Built In's interface for alerts is at **Account → Email Preferences**.

---

## 7. Wellfound (formerly AngelList Talent)

Startups; biased toward Y Combinator and AngelList alumni.

1. Go to https://wellfound.com/ → sign in.
2. **Jobs** → filter: **Internship**.
3. Keywords: `software engineer`, `ML engineer`, `embedded`.
4. Click **Save filters** and enable email notifications in your account settings.

Note: Wellfound's intern coverage is thin compared to LinkedIn but the role quality is high (post-Series-A startups, not just any company).

---

## 8. YC Work at a Startup

YC portfolio companies. Direct firehose to founders, no recruiter middleman.

1. Go to https://www.workatastartup.com/ → create account → verify email.
2. **Jobs** → **Filters** → **Role: Internship**.
3. Optional: limit to specific role buckets (Engineering, ML/AI, Data Science).
4. **Save search** → enable weekly digest in account settings (no daily option as of last check).

YC's internship volume is seasonal — heavy in late fall through early spring for following-year summer/fall placements.

---

## 9. Otta / Welcome to the Jungle

Otta was acquired by Welcome to the Jungle in 2024. The interface is curated and worth checking even at lower volume.

1. Go to https://welcometothejungle.com/ → create account.
2. Set preferences: **Internship**, locations: Remote, Boston, DC, NYC.
3. Enable **Weekly digest** in notification settings.

---

## 10. Defense prime Workday portals

The defense primes (Lockheed, Northrop, RTX, General Dynamics, Booz Allen, Leidos, MITRE, MIT Lincoln Lab) post a high volume of cleared intern roles directly to their own Workday tenants. None of them surface fully on aggregators.

Each requires a separate account. Set up **Job alert** on each after running an "intern" search. Frequency: **Weekly** for the primes (they batch announcements); **Daily** for the smaller ones.

| Employer | Portal | Notes |
|----------|--------|-------|
| Lockheed Martin | https://www.lockheedmartinjobs.com/ | Big intern program; Bethesda, Sunnyvale, Denver hubs |
| Northrop Grumman | https://www.northropgrumman.com/careers | Cleared intern programs in DC, LA, MD |
| Raytheon Technologies (RTX) | https://careers.rtx.com/ | Includes Collins, Pratt; New England + AZ |
| General Dynamics | https://www.gd.com/careers | Several subsidiaries, search each |
| Booz Allen Hamilton | https://www.boozallen.com/careers | DC-heavy, cleared focus |
| Leidos | https://careers.leidos.com/ | DC + Reston |
| MITRE | https://www.mitre.org/careers | Federally Funded R&D Center; intern program lives at https://www.mitre.org/careers/students-grads |
| MIT Lincoln Lab | https://www.ll.mit.edu/careers | Lexington, MA; great for Boston + cleared |
| The Aerospace Corp | https://aerospace.org/careers | El Segundo CA + Chantilly VA |
| Draper Lab | https://www.draper.com/careers | Cambridge, MA — close to Penn-Boston relocations |

**Bulk efficiency move:** For each portal, set the alert to forward to a `Jobs/Alerts/Primes` label so they don't clutter the main inbox. See `GMAIL_FILTERS.md`.

---

## 11. Dice

Dice is the legacy tech jobs board. Lower signal than LinkedIn but useful for cleared roles.

1. Go to https://www.dice.com/ → create account.
2. **Search** → `intern` + your category keywords.
3. Save searches with daily alerts.

---

## Verification checklist

After setting up the platforms above, by tomorrow morning you should have:

- [ ] 3 USAJobs daily alerts
- [ ] 5-7 LinkedIn daily alerts
- [ ] 1 Handshake daily digest
- [ ] 1 ClearanceJobs daily alert
- [ ] 1 ClearedJobs.net daily alert
- [ ] 2-3 Built In daily alerts
- [ ] 1 Wellfound + 1 YC weekly digest
- [ ] 1 Welcome to the Jungle weekly digest
- [ ] 10 defense-prime alerts (weekly cadence for most)

Total emails per week: ~30-50 alerts across all sources. Filter discipline (next doc) is what makes this manageable.

## Common pitfalls

- **Alert overload.** You'll get bombarded the first week. Don't disable alerts; tighten the search queries instead. "software engineer intern" returns less noise than "software intern".
- **Duplicates across platforms.** A LinkedIn alert and an Adzuna posting from Dragnet often point at the same role. That's fine — the dedup in Layer 2 doesn't dedup against Layer 1 emails. Treat the email as a notification, not as a separate item.
- **Workday-portal alerts breaking after password rotations.** Some primes auto-expire alerts when you rotate passwords. Re-enable quarterly.
- **Saved searches that drift.** A saved search you wrote in Phase 3 may bring nothing relevant by Phase 5. Audit and rewrite at the end of each verification week (Phase 4).
