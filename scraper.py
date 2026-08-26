import requests
import re
from config import TITLE_KEYWORDS, LOCATION_KEYWORDS

GREENHOUSE_API_URL = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
REQUEST_TIMEOUT_SECONDS = 10


def fetch_postings_for_company(slug: str) -> list[dict]:
    url = GREENHOUSE_API_URL.format(slug=slug)
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"[scraper] failed to fetch postings for '{slug}': {exc}")
        return []

    data = response.json()
    raw_jobs = data.get("jobs", [])

    postings = []
    for job in raw_jobs:
        postings.append(
            {
                "company": slug,
                "title": job.get("title", "").strip(),
                "location": (job.get("location") or {}).get("name", ""),
                "url": job.get("absolute_url", ""),
                "date_posted": job.get("updated_at", ""),
            }
        )
    return postings


def matches_filters(posting: dict) -> bool:
    title = posting["title"].lower()
    title_ok = any(
        re.search(rf"\b{re.escape(keyword.lower())}\b", title)
        for keyword in TITLE_KEYWORDS
    )
    if not title_ok:
        return False

    if not LOCATION_KEYWORDS:
        return True

    location = (posting.get("location") or "").lower()
    return any(keyword.lower() in location for keyword in LOCATION_KEYWORDS)


def fetch_all_matching_postings(company_slugs: list[str]) -> list[dict]:
    all_matches = []
    for slug in company_slugs:
        postings = fetch_postings_for_company(slug)
        matches = [p for p in postings if matches_filters(p)]
        print(f"[scraper] {slug}: {len(postings)} postings, {len(matches)} match filters")
        all_matches.extend(matches)
    return all_matches