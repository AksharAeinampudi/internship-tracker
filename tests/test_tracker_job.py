"""Deduplication by URL and the "notified" flag.

The scrape uses saved sample responses and the email sender is a fake, so nothing
leaves the machine.
"""

import pytest
from sqlalchemy.exc import IntegrityError

from models import Posting, db
from tracker_job import run_tracker_job

# The sample boards hold 7 postings; 4 have "intern"/"internship" in the title.
MATCHING_URLS = {
    "https://boards.greenhouse.io/examplegh/jobs/7001",
    "https://boards.greenhouse.io/examplegh/jobs/7003",
    "https://jobs.lever.co/examplelever/a1b2c3",
    "https://jobs.lever.co/examplelever/g7h8i9",
}


def all_postings(app) -> list[Posting]:
    with app.app_context():
        return Posting.query.all()


def test_database_rejects_a_second_posting_with_the_same_url(flask_app):
    with flask_app.app_context():
        db.session.add(Posting(company="a", title="Intern", url="https://example.com/1"))
        db.session.commit()
        db.session.add(Posting(company="b", title="Other Intern", url="https://example.com/1"))
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        assert Posting.query.count() == 1


def test_first_run_stores_only_matching_postings(flask_app, fake_boards, fake_email):
    result = run_tracker_job(flask_app)

    assert result == {"scraped": 4, "new": 4}
    postings = all_postings(flask_app)
    assert {p.url for p in postings} == MATCHING_URLS
    assert all(p.status == "new" for p in postings)


def test_rerunning_does_not_duplicate_postings(flask_app, fake_boards, fake_email):
    run_tracker_job(flask_app)
    second = run_tracker_job(flask_app)

    assert second == {"scraped": 4, "new": 0}
    assert len(all_postings(flask_app)) == 4


def test_same_url_twice_in_one_scrape_is_stored_once(flask_app, fake_boards, fake_email):
    jobs = fake_boards[next(u for u in fake_boards if "greenhouse" in u)]["jobs"]
    jobs.append(dict(jobs[0]))  # the board lists the same job twice

    result = run_tracker_job(flask_app)

    assert result["scraped"] == 5
    assert result["new"] == 4
    assert len(all_postings(flask_app)) == 4


def test_rescrape_keeps_the_application_status(flask_app, fake_boards, fake_email):
    run_tracker_job(flask_app)
    with flask_app.app_context():
        posting = Posting.query.filter_by(url="https://jobs.lever.co/examplelever/a1b2c3").one()
        posting.status = "applied"
        db.session.commit()

    run_tracker_job(flask_app)

    with flask_app.app_context():
        posting = Posting.query.filter_by(url="https://jobs.lever.co/examplelever/a1b2c3").one()
        assert posting.status == "applied"


def test_new_postings_are_emailed_once_and_marked_notified(flask_app, fake_boards, fake_email):
    run_tracker_job(flask_app)

    assert len(fake_email.calls) == 1
    assert {p["url"] for p in fake_email.calls[0]} == MATCHING_URLS
    assert all(p.notified for p in all_postings(flask_app))


def test_second_run_sends_no_email_when_nothing_is_new(flask_app, fake_boards, fake_email):
    run_tracker_job(flask_app)
    run_tracker_job(flask_app)

    assert len(fake_email.calls) == 1


def test_only_the_new_posting_is_emailed(flask_app, fake_boards, fake_email):
    run_tracker_job(flask_app)
    lever_url = next(u for u in fake_boards if "lever" in u)
    fake_boards[lever_url].append(
        {
            "text": "Design Intern",
            "hostedUrl": "https://jobs.lever.co/examplelever/new1",
            "categories": {"location": "Remote"},
        }
    )

    result = run_tracker_job(flask_app)

    assert result["new"] == 1
    assert len(fake_email.calls) == 2
    assert [p["url"] for p in fake_email.calls[1]] == ["https://jobs.lever.co/examplelever/new1"]


def test_failed_email_leaves_postings_not_notified(flask_app, fake_boards, fake_email):
    fake_email.succeed = False

    result = run_tracker_job(flask_app)

    assert result["new"] == 4  # postings are still saved
    assert not any(p.notified for p in all_postings(flask_app))


def test_no_email_when_scrape_finds_nothing(flask_app, fake_boards, fake_email):
    for payload in fake_boards.values():
        if isinstance(payload, dict):
            payload["jobs"] = []
        else:
            payload.clear()

    assert run_tracker_job(flask_app) == {"scraped": 0, "new": 0}
    assert fake_email.calls == []
