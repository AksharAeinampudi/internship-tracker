"""Shared test setup.

The environment is pinned *before* any app module is imported, so a developer's real
`.env` (database URL, email credentials) is never used by the tests: python-dotenv does
not override variables that are already set.
"""

import json
import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite://"  # in-memory
os.environ["SMTP_USERNAME"] = ""
os.environ["SMTP_PASSWORD"] = ""
os.environ["NOTIFY_TO_EMAIL"] = ""
os.environ.pop("RUN_SCHEDULER", None)

import pytest  # noqa: E402
import requests  # noqa: E402

import notifier  # noqa: E402
import scraper  # noqa: E402
import tracker_job  # noqa: E402
from app import create_app  # noqa: E402
from models import db  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"
GREENHOUSE_SLUG = "examplegh"
LEVER_SLUG = "examplelever"


def load_fixture(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class FakeResponse:
    def __init__(self, payload, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error")

    def json(self):
        return self._payload


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Fail loudly if any test tries to reach the internet or an SMTP server."""

    def blocked_get(*args, **kwargs):
        raise AssertionError(f"unexpected HTTP request: {args!r}")

    def blocked_smtp(*args, **kwargs):
        raise AssertionError("unexpected SMTP connection")

    monkeypatch.setattr(scraper.requests, "get", blocked_get)
    monkeypatch.setattr(notifier.smtplib, "SMTP", blocked_smtp)


@pytest.fixture
def fake_boards(monkeypatch):
    """Serve the saved Greenhouse and Lever sample responses instead of the real APIs.

    Returns the dict of URL -> payload so a test can change what a board returns.
    """
    responses = {
        scraper.GREENHOUSE_API_URL.format(slug=GREENHOUSE_SLUG): load_fixture(
            "greenhouse_jobs.json"
        ),
        scraper.LEVER_API_URL.format(slug=LEVER_SLUG): load_fixture("lever_postings.json"),
    }

    def fake_get(url, timeout=None):
        if url not in responses:
            return FakeResponse({}, status_code=404)
        return FakeResponse(responses[url])

    monkeypatch.setattr(scraper.requests, "get", fake_get)
    monkeypatch.setattr(tracker_job, "GREENHOUSE_COMPANY_SLUGS", [GREENHOUSE_SLUG])
    monkeypatch.setattr(tracker_job, "LEVER_COMPANY_SLUGS", [LEVER_SLUG])
    return responses


class FakeEmailSender:
    """Stands in for notifier.send_new_postings_email and records each call."""

    def __init__(self) -> None:
        self.calls: list[list[dict]] = []
        self.succeed = True

    def __call__(self, postings: list[dict]) -> bool:
        self.calls.append(postings)
        return self.succeed


@pytest.fixture
def fake_email(monkeypatch) -> FakeEmailSender:
    sender = FakeEmailSender()
    monkeypatch.setattr(tracker_job, "send_new_postings_email", sender)
    return sender


@pytest.fixture
def flask_app():
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite://", "TESTING": True})
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(flask_app):
    return flask_app.test_client()
