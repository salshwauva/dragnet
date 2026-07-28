# Gmail filter setup

The Layer 1 native alerts emit ~30-50 emails per week. Without filters, this drowns your inbox. With filters, alerts route to `Jobs/Alerts/<source>` labels and stay out of the main inbox until you triage them.

## Label structure

Create these labels (Settings → Labels → Create new label, with nesting):

```
Jobs/
├── Alerts/
│   ├── USAJobs
│   ├── LinkedIn
│   ├── Handshake
│   ├── ClearanceJobs
│   ├── ClearedJobs
│   ├── BuiltIn
│   ├── Wellfound
│   ├── YC
│   ├── WTTJ        (Welcome to the Jungle)
│   ├── Primes      (Lockheed, Northrop, RTX, etc.)
│   ├── Dice
│   └── Dragnet     (the email digest from Layer 2)
├── Applications/
└── Responses/
```

Top-level `Jobs/` holds applications and responses you'll manage with the `job-app-tracker` skill. `Jobs/Alerts/*` is the firehose; `Jobs/Applications/*` and `Jobs/Responses/*` come later in the lifecycle.

## Filter rules

Gmail filter syntax: Settings → Filters and Blocked Addresses → Create a new filter. For each row below, paste the **From / Has the words** value into the matching field, then on the next screen check **Skip the Inbox** + **Apply the label** for the destination label.

| # | Source | From / Has the words | Label |
|---|--------|----------------------|-------|
| 1 | USAJobs | `from:(usajobs@usajobs.gov OR donotreply@usajobs.gov OR jobalerts@usajobs.gov)` | `Jobs/Alerts/USAJobs` |
| 2 | LinkedIn | `from:(jobs-noreply@linkedin.com OR jobalerts-noreply@linkedin.com OR jobs-listings@linkedin.com)` | `Jobs/Alerts/LinkedIn` |
| 3 | Handshake | `from:(@joinhandshake.com OR @handshake.com)` | `Jobs/Alerts/Handshake` |
| 4 | ClearanceJobs | `from:(@clearancejobs.com)` | `Jobs/Alerts/ClearanceJobs` |
| 5 | ClearedJobs.net | `from:(@clearedjobs.net OR @clearedconnections.com)` | `Jobs/Alerts/ClearedJobs` |
| 6 | Built In | `from:(@builtin.com OR notifications@builtin.com)` | `Jobs/Alerts/BuiltIn` |
| 7 | Wellfound | `from:(@wellfound.com OR @angel.co)` | `Jobs/Alerts/Wellfound` |
| 8 | YC Work at a Startup | `from:(@workatastartup.com OR @ycombinator.com) subject:(intern OR jobs)` | `Jobs/Alerts/YC` |
| 9 | Welcome to the Jungle | `from:(@welcometothejungle.com)` | `Jobs/Alerts/WTTJ` |
| 10 | Defense primes | `from:(@lockheedmartin.com OR @northropgrumman.com OR @rtx.com OR @gd.com OR @boozallen.com OR @leidos.com OR @mitre.org OR @ll.mit.edu OR @draper.com OR @aerospace.org)` | `Jobs/Alerts/Primes` |
| 11 | Dice | `from:(@dice.com)` | `Jobs/Alerts/Dice` |
| 12 | Dragnet (your own scraper) | `subject:[Dragnet]` | `Jobs/Alerts/Dragnet` |

For filters 1-11, also check:
- ✅ **Skip the Inbox (Archive it)**
- ✅ **Apply the label** (as above)
- ✅ **Never send it to Spam**
- ⬜ **Mark as read** (intentionally unchecked — you want unread badges on the labels)

For filter 12 (your own Dragnet digest), check:
- ⬜ **Skip the Inbox** (intentionally unchecked — keep this one in the inbox; it's the daily action item)
- ✅ **Apply the label**
- ✅ **Never send it to Spam**

## Triage workflow

Once a day (e.g. with morning coffee), open the labels and triage:

1. Click `Jobs/Alerts/Dragnet` first — your highest-signal source. Top 5 by score.
2. Then `Jobs/Alerts/USAJobs` and `Jobs/Alerts/ClearanceJobs` — high-signal cleared roles.
3. Then `Jobs/Alerts/Handshake` — Penn-specific, often direct.
4. Then `Jobs/Alerts/Primes` — slow cadence, scan for new programs.
5. Skim `Jobs/Alerts/LinkedIn` last — high volume, lower signal-per-email.

For any role you want to apply to: hand it to the `job-apps` skill in Claude. That skill drafts the cover letter and CV tweaks, then hands off to `job-app-tracker` which logs the application in your vault.

## Maintenance

- **Weekly:** check `Jobs/Alerts/*` unread counts. If one label has zero unreads for 2+ weeks, either the search is too narrow or the source is dormant — review.
- **Monthly:** re-evaluate any filter labeled at high volume but low conversion (you never apply to anything in it). The native alert is probably miscalibrated.
- **Quarterly:** rotate the searches on each source. Job boards change their indexing; queries that worked in Q1 are stale by Q4.

## Quick verification

After creating all filters, send yourself a test email with subject `[Dragnet] test` from the Gmail address you'll use for the digest. It should land in `Jobs/Alerts/Dragnet` AND stay in the inbox.
