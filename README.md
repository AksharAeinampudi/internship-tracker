# Internship Tracker

[![CI](https://github.com/AksharAeinampudi/internship-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/AksharAeinampudi/internship-tracker/actions/workflows/ci.yml)

A Flask app that scrapes internship postings from companies' public **Greenhouse** and **Lever** job boards, stores them in a database, lets you track your application status per posting, and emails you when new matching postings show up.

## Why Greenhouse and Lever?

Many companies host their public job listings on Greenhouse or Lever, both of which expose clean, public, no-login-required JSON APIs. That makes them good, ToS-friendly sources for a project like this, unlike sites such as LinkedIn or Handshake, which require login and actively block automated scraping.

## Features

- Scrapes multiple companies across **two different job board platforms** (Greenhouse and Lever), each with their own API response shape, normalized into one consistent internal format
- Filters postings by keyword using word-boundary matching (e.g. correctly excludes "Internal Audit" when searching for "intern")
- Stores postings in SQLite locally or Postgres in production, with deduplication by URL enforced both in the application and by a unique constraint in the database
- Web UI to view postings, filter them by status, and update your application status (new / applied / interviewing / rejected / offer)
- Emails you a digest of new matching postings. Because postings are deduplicated by URL, each posting appears in at most one email; a `notified` flag records whether that email actually went out
- Scrapes on demand via the "Refresh now" button, on a schedule from an in-process scheduler (local), or from a scheduled GitHub Actions job (production)
- 48 pytest tests that run on saved API responses, a fake email sender and an in-memory database, so they never touch the network; GitHub Actions runs them on every push and pull request

## Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # then fill in your email credentials
```

Edit `config.py` to set which companies to track and what keywords count as a match:
- `GREENHOUSE_COMPANY_SLUGS` — find a company's slug from the URL of their public Greenhouse careers page, e.g. `boards.greenhouse.io/stripe` → slug is `stripe`
- `LEVER_COMPANY_SLUGS` — find a company's slug the same way, from `jobs.lever.co/<slug>`
- `TITLE_KEYWORDS`, `LOCATION_KEYWORDS` — adjust to fit what you're looking for

For email, Gmail works well with an [App Password](https://myaccount.google.com/apppasswords) (requires 2-factor auth on the account) — don't use your real Gmail password.

## Run it

```bash
python app.py
```

Visit `http://127.0.0.1:5000`. Click "Refresh now" to run a scrape immediately. To also scrape automatically every `SCRAPE_INTERVAL_HOURS` hours while the app is running, set `RUN_SCHEDULER=true` in `.env`.

To run a single scrape from the command line (this is what the scheduled job in production does):

```bash
python tracker_job.py
```

## Tests

```bash
pytest
```

The tests live in `tests/`. Sample Greenhouse and Lever responses are in `tests/fixtures/`; any test that tries to make a real HTTP request or open a real SMTP connection fails. The tests set their own environment before the app is imported, so your `.env` (database, email password) is never used.

## Deploy (free)

### What a free host means for this app

Free web services (Render, Railway, Fly.io and similar) have two limits that matter here:

- **The disk is temporary.** Files written while the app runs, including a SQLite database in `instance/`, are wiped on every deploy and restart. Your postings and application statuses would disappear. So production uses a hosted **Postgres** database instead. [Neon](https://neon.tech) has a free tier that does not expire (Render's own free Postgres is deleted after 30 days).
- **The service sleeps when nobody visits it** (Render: after 15 minutes idle; the next visit takes up to about a minute to wake it). The in-process scheduler runs inside the web server, so it sleeps too and the scheduled scrape would rarely run. So production runs the scrape from **GitHub Actions** on a timer instead (`.github/workflows/scrape.yml`, every 6 hours). It runs `python tracker_job.py` against the same Postgres database and sends the email. Leave `RUN_SCHEDULER` unset on the web service.

The result: Neon holds the data, GitHub Actions does the scraping and emailing, and the Render web service is only the UI (view postings, change status, "Refresh now").

```
GitHub Actions (every 6 h) ──scrape + email──▶ Neon Postgres ◀──read/update── Render web service (UI)
```

### Steps

1. **Push the code to GitHub** (the repo must be on GitHub for both Render and Actions).
2. **Create the database on Neon.** Sign in at neon.tech, create a new project (pick the AWS US East 2 / Ohio region so it is close to the Render service), and copy the connection string. It looks like `postgresql://user:password@ep-....us-east-2.aws.neon.tech/neondb?sslmode=require`. The app rewrites `postgres://` / `postgresql://` URLs to the psycopg 3 driver itself, so paste it as is. Tables are created automatically on first start.
3. **Create the web service on Render.** In the Render dashboard choose **New → Blueprint**, pick this repository, and Render reads `render.yaml` (free plan, Ohio region, Python 3.12). When it asks for the secret values, paste:
   - `DATABASE_URL`: the Neon connection string
   - `SMTP_USERNAME`, `SMTP_PASSWORD`, `NOTIFY_TO_EMAIL`: optional; only used when you press "Refresh now" on the site. Leave them empty if you only want the scheduled emails.

   Without the blueprint, create a **Web Service** by hand with build command `pip install -r requirements.txt`, start command `gunicorn app:app --workers 1 --threads 4 --timeout 120`, and the same environment variables plus `PYTHON_VERSION=3.12.8`.
4. **Add the scrape job's secrets on GitHub.** In the repository go to **Settings → Secrets and variables → Actions → New repository secret** and add `DATABASE_URL` (the same Neon string), `SMTP_USERNAME`, `SMTP_PASSWORD` (the Gmail app password) and `NOTIFY_TO_EMAIL`. Until `DATABASE_URL` is set, the scheduled job skips itself instead of failing.
5. **Test it.** Open the Render URL and check the page loads. Then in GitHub go to **Actions → Scheduled scrape → Run workflow**; when it finishes, refresh the site to see the postings.

### Things to know

- **Gunicorn runs one worker with four threads.** The app creates its tables at startup and can start a scheduler; one process means that happens once. Render's free instance is small, so more processes would not help anyway. The 120 s timeout leaves room for "Refresh now", which scrapes every board before it answers.
- **GitHub's scheduled jobs are best effort.** A run can start several minutes late. In a public repository GitHub turns scheduled workflows off after 60 days without any commits; re-enable it from the Actions tab. Public repositories have unlimited Actions minutes; in a private one each run uses about a minute of the 2,000 free minutes a month.
- **The site has no login.** Anyone with the URL can see your list, change statuses and press "Refresh now". Keep the URL to yourself, or add authentication first (see next steps).
- **Local data does not move to production.** The deployed app starts with an empty database and fills it on the first scrape.

## Project structure

```
app.py              Flask app factory and routes (list, filter, update status, refresh)
config.py           Settings read from environment variables; companies and keywords
scraper.py          Greenhouse and Lever clients, normalization, keyword filtering
models.py           Posting table (unique URL, status, notified flag)
tracker_job.py      One scrape: fetch, dedupe, save, email; `python tracker_job.py` runs it once
notifier.py         SMTP email digest
scheduler.py        Optional in-process APScheduler job (RUN_SCHEDULER=true)
templates/          Bootstrap UI
tests/              pytest suite and saved API responses (tests/fixtures/)
Procfile            Production start command (gunicorn)
render.yaml         Render blueprint for the web service
.github/workflows/  ci.yml runs the tests; scrape.yml runs the scheduled scrape
```

## What I learned building this

- Integrating two different external APIs with different data shapes (Greenhouse nests postings under a `"jobs"` key with `location.name`; Lever returns a flat list with `categories.location`, a `text` field for the title, and millisecond Unix timestamps) while keeping the rest of the app source-agnostic
- A real bug I found through testing, not assumption: my first filtering approach used plain substring matching, which incorrectly matched "Internal Audit" when searching for "intern." Fixed with a word-boundary regex (`\bintern\b`)
- Designing a simple relational schema and enforcing uniqueness (dedupe postings by URL) at the database level instead of relying only on application code
- Sending email programmatically via SMTP, including handling failures gracefully so a bad email doesn't crash the whole job
- Testing code that talks to outside services by replacing them with saved responses and fakes, so the tests are fast and can't spam anyone
- Why a background scheduler inside a web server doesn't fit a free host that sleeps and has a temporary disk, and moving the data to hosted Postgres and the schedule to a separate job instead

## Possible next steps

- Add a login (even a single shared password) before sharing the deployed URL
- Retry failed emails: postings whose email failed keep `notified = false` but are not included in later emails yet
- Move the company list and keywords from `config.py` into the database so they can be edited from the UI
- Replace `print` with `logging`, and the deprecated `datetime.utcnow` / `utcfromtimestamp` calls with timezone-aware ones
- Add more companies across both platforms
- Add a "days since posted" or "days since applied" column
