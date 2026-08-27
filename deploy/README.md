# Deploying (free, no server)

The site runs entirely on GitHub — no VPS, no credit card, nothing to keep
alive.

```
GitHub Actions (cron)  ->  runs the model, commits a reading to data/
data/recent.json       ->  the "database", read straight from the repo
GitHub Pages           ->  serves the React build
```

An always-on server would cost ~$5/mo mostly to keep a 1 GB PyTorch process
resident. A scheduled job avoids that: it starts, takes one reading, and
exits. Public repos get unlimited Actions minutes.

## Setup

**1. Push to a public GitHub repo.** Public matters — that's what makes the
Actions minutes free.

**2. Enable Pages.** Settings → Pages → Source: **GitHub Actions**.

**3. Allow Actions to push.** Settings → Actions → General → Workflow
permissions: **Read and write**. The collector commits each reading, and
without this it fails at the push step.

**4. Run it once by hand.** Actions tab → *Collect reading* → *Run workflow*.
Takes ~2 minutes on the first run (installing PyTorch); after that the pip
cache makes it faster. Check that a `data/recent.json` commit appears.

**5. Deploy the site.** Actions tab → *Deploy site* → *Run workflow*. It
lands at `https://<username>.github.io/<repo>/`.

## How the two workflows fit together

`collect.yml` runs every 10 minutes during gym hours and commits a reading.

`pages.yml` rebuilds the site — but only on changes under `frontend/`. That
`paths:` filter matters: without it, every data commit would trigger a
deploy, hundreds a day.

The frontend never rebuilds for new data because it fetches
`data/recent.json` from `raw.githubusercontent.com` at runtime.

## The real tradeoff

GitHub's minimum cron interval is 5 minutes, and scheduled runs are queued
on a best-effort basis — under load they're routinely 10–20 minutes late,
and occasionally skipped. So this is a ~15-minute-resolution tracker, not a
live one.

For "how busy is the gym," that's fine. Occupancy doesn't move much in 15
minutes, and hour-of-week patterns are unaffected. What you give up is the
"updated 30 seconds ago" feel.

Also: **GitHub disables scheduled workflows after 60 days of repository
inactivity.** The collector's own commits normally count as activity, but
it's worth checking every couple of months.

## Data layout

| Path | What |
| --- | --- |
| `data/recent.json` | Last 48h plus the current reading — what the page loads |
| `data/history/YYYY-MM.json` | Permanent archive, one file per month |

At ~100 readings/day the archive grows about 1 MB/year.

## Running the collector locally

```
cd backend && source .venv/bin/activate
python -m app.collect
```

Writes to the same files the workflow does. Useful for backfilling or
testing changes to the detector.

## Note on the frame endpoint

`/api/frame` (annotated photos with people boxed) only exists on the local
FastAPI server. The deployed site publishes counts, not images — publishing
identifiable people is a different proposition from publishing a headcount.
The button hides itself when the endpoint isn't there.

## If you later want true real-time

The original always-on design still works — `app/main.py` runs the poll loop
in-process. It needs a box with **2 GB RAM** (inference peaks at ~1 GB; a
1 GB instance gets OOM-killed). Hetzner CX22 is ~€4/mo. You'd run it under
systemd behind Caddy for TLS; `uf-gym-tracker.service` and `Caddyfile` in
this directory are set up for that.
