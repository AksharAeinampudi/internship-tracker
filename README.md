# Internship Tracker

A Flask app that scrapes internship postings from companies' public **Greenhouse** and **Lever** job boards, stores them in a database, lets you track your application status per posting, and emails you when new matching postings show up.

## Why Greenhouse and Lever?

Many companies host their public job listings on Greenhouse or Lever, both of which expose clean, public, no-login-required JSON APIs. That makes them good, ToS-friendly sources for a project like this, unlike sites such as LinkedIn or Handshake, which require login and actively block automated scraping.

## Features

- Scrapes multiple companies across **two different job board platforms** (Greenhouse and Lever), each with their own API response shape, normalized into one consistent internal format
- Filters postings by keyword using word-boundary matching (e.g. correctly excludes "Internal Audit" when searching for "intern")
- Stores postings in a SQLite database, with deduplication enforced at both the application and database level
- Web UI to view postings and update your application status (new / applied / interviewing / rejected / offer)
- Emails you when new matching postings are found, using an idempotent "notified" flag so you're never emailed about the same posting twice
- Runs on a schedule in the background (every N hours), or on demand via the "Refresh now" button

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

Visit `http://127.0.0.1:5000`. Click "Refresh now" to run a scrape immediately, or let the background scheduler do it automatically every `SCRAPE_INTERVAL_HOURS` hours (set in `.env`).

## Project structure


## What I learned building this

- Integrating two different external APIs with different data shapes (Greenhouse nests postings under a `"jobs"` key with `location.name`; Lever returns a flat list with `categories.location`, a `text` field for the title, and millisecond Unix timestamps) while keeping the rest of the app source-agnostic
- A real bug I found through testing, not assumption: my first filtering approach used plain substring matching, which incorrectly matched "Internal Audit" when searching for "intern." Fixed with a word-boundary regex (`\bintern\b`)
- Designing a simple relational schema and enforcing uniqueness (dedupe postings by URL) at the database level instead of relying only on application code
- Sending email programmatically via SMTP, including handling failures gracefully so a bad email doesn't crash the whole job
- Running background/scheduled tasks alongside a web server
- Structuring a Flask app into separate, testable modules instead of one big file

## Possible next steps

- Add automated tests, especially for the filtering logic
- Add more companies across both platforms
- Deploy it (Render/Railway/Fly.io all have free tiers) so it runs even when your laptop is off
- Add a "days since posted" or "days since applied" column