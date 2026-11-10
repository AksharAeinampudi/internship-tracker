"""Greenhouse and Lever responses are normalized into one posting format.

All HTTP calls go to saved sample responses in tests/fixtures (see conftest.fake_boards).
"""

import requests

import scraper
from conftest import GREENHOUSE_SLUG, LEVER_SLUG

POSTING_KEYS = {"company", "title", "location", "url", "date_posted"}


def test_greenhouse_jobs_are_normalized(fake_boards):
    postings = scraper.fetch_postings_for_company(GREENHOUSE_SLUG)

    assert len(postings) == 4
    assert all(set(p) == POSTING_KEYS for p in postings)
    assert postings[0] == {
        "company": GREENHOUSE_SLUG,
        "title": "Software Engineering Intern, Summer 2027",  # surrounding spaces stripped
        "location": "San Francisco, CA",  # from the nested location.name
        "url": "https://boards.greenhouse.io/examplegh/jobs/7001",
        "date_posted": "2026-10-30T12:00:00-04:00",
    }


def test_greenhouse_null_location_becomes_empty_string(fake_boards):
    postings = scraper.fetch_postings_for_company(GREENHOUSE_SLUG)
    data_science = next(p for p in postings if p["title"] == "Data Science Internship")
    assert data_science["location"] == ""


def test_lever_postings_are_normalized(fake_boards):
    postings = scraper.fetch_postings_for_lever_company(LEVER_SLUG)

    assert len(postings) == 3
    assert all(set(p) == POSTING_KEYS for p in postings)
    assert postings[0] == {
        "company": LEVER_SLUG,
        "title": "Marketing Intern",  # Lever calls the title "text"
        "location": "Boston, MA",  # from categories.location
        "url": "https://jobs.lever.co/examplelever/a1b2c3",
        # createdAt is milliseconds since the epoch: 1761955200000 ms = 2025-11-01 00:00 UTC
        "date_posted": "2025-11-01T00:00:00",
    }


def test_lever_posting_without_categories_or_date(fake_boards):
    postings = scraper.fetch_postings_for_lever_company(LEVER_SLUG)
    bare = postings[2]
    assert bare["title"] == "Engineering Intern"
    assert bare["location"] == ""
    assert bare["date_posted"] == ""


def test_failed_request_returns_no_postings(monkeypatch):
    def failing_get(url, timeout=None):
        raise requests.ConnectionError("board is down")

    monkeypatch.setattr(scraper.requests, "get", failing_get)
    assert scraper.fetch_postings_for_company("anything") == []
    assert scraper.fetch_postings_for_lever_company("anything") == []


def test_http_error_returns_no_postings(fake_boards):
    # fake_boards answers 404 for any company it doesn't know
    assert scraper.fetch_postings_for_company("unknown-company") == []
    assert scraper.fetch_postings_for_lever_company("unknown-company") == []


def test_fetch_all_combines_both_sources_and_filters(fake_boards):
    matches = scraper.fetch_all_matching_postings([GREENHOUSE_SLUG], [LEVER_SLUG])

    titles = sorted(p["title"] for p in matches)
    assert titles == [
        "Data Science Internship",
        "Engineering Intern",
        "Marketing Intern",
        "Software Engineering Intern, Summer 2027",
    ]
    # "Internal Audit Lead", "Senior Backend Engineer" and "Account Executive" are dropped
    assert {p["company"] for p in matches} == {GREENHOUSE_SLUG, LEVER_SLUG}


def test_one_failing_board_does_not_stop_the_others(fake_boards):
    matches = scraper.fetch_all_matching_postings(["unknown-company", GREENHOUSE_SLUG], [])
    assert len(matches) == 2
