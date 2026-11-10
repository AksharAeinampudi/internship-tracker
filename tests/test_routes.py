"""Flask routes: viewing postings, filtering by status, updating status, refreshing."""

from datetime import datetime

import pytest

from models import Posting, db


@pytest.fixture
def seeded(flask_app):
    """Three postings scraped on different days; returns their ids by title."""
    rows = [
        ("Older Intern", "https://example.com/older", datetime(2026, 10, 1), "applied"),
        ("Newest Intern", "https://example.com/newest", datetime(2026, 10, 20), "new"),
        ("Middle Intern", "https://example.com/middle", datetime(2026, 10, 10), "new"),
    ]
    with flask_app.app_context():
        for title, url, scraped, status in rows:
            db.session.add(
                Posting(company="acme", title=title, url=url, date_scraped=scraped, status=status)
            )
        db.session.commit()
        return {p.title: p.id for p in Posting.query.all()}


def status_of(flask_app, posting_id: int) -> str:
    with flask_app.app_context():
        return db.session.get(Posting, posting_id).status


def test_index_shows_empty_state(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "No postings yet" in response.get_data(as_text=True)


def test_index_lists_postings_newest_first(client, seeded):
    html = client.get("/").get_data(as_text=True)
    assert html.index("Newest Intern") < html.index("Middle Intern") < html.index("Older Intern")
    assert "Oct 20, 2026" in html


def test_index_filters_by_status(client, seeded):
    html = client.get("/?status=applied").get_data(as_text=True)
    assert "Older Intern" in html
    assert "Newest Intern" not in html
    assert "Middle Intern" not in html


def test_update_status_saves_and_redirects(client, flask_app, seeded):
    posting_id = seeded["Newest Intern"]

    response = client.post(f"/postings/{posting_id}/status", data={"status": "interviewing"})

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    assert status_of(flask_app, posting_id) == "interviewing"


def test_update_status_ignores_unknown_values(client, flask_app, seeded):
    posting_id = seeded["Newest Intern"]

    response = client.post(f"/postings/{posting_id}/status", data={"status": "hired!!"})

    assert response.status_code == 302
    assert status_of(flask_app, posting_id) == "new"


def test_update_status_of_missing_posting_is_404(client, seeded):
    response = client.post("/postings/9999/status", data={"status": "applied"})
    assert response.status_code == 404


def test_refresh_runs_the_job_and_returns_counts(client, fake_boards, fake_email):
    response = client.post("/refresh")

    assert response.status_code == 200
    assert response.get_json() == {"scraped": 4, "new": 4}
    assert "Data Science Internship" in client.get("/").get_data(as_text=True)


def test_refresh_only_accepts_post(client):
    assert client.get("/refresh").status_code == 405
