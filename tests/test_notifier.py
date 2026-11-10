"""The email sender, with a fake SMTP server in place of a real one."""

import smtplib

import pytest

import notifier

POSTINGS = [
    {
        "title": "Software Engineering Intern",
        "company": "examplegh",
        "location": "Remote",
        "url": "https://boards.greenhouse.io/examplegh/jobs/1",
    },
    {
        "title": "Marketing Intern",
        "company": "examplelever",
        "location": None,
        "url": "https://jobs.lever.co/examplelever/2",
    },
]


class FakeSMTP:
    """Records what would have been sent. One instance per connection."""

    instances: list["FakeSMTP"] = []
    fail_on_send = False

    def __init__(self, host, port):
        self.host, self.port = host, port
        self.started_tls = False
        self.logged_in_as = None
        self.sent = []
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self):
        self.started_tls = True

    def login(self, username, password):
        self.logged_in_as = username

    def sendmail(self, from_addr, to_addr, message):
        if FakeSMTP.fail_on_send:
            raise smtplib.SMTPException("server said no")
        self.sent.append((from_addr, to_addr, message))


@pytest.fixture
def fake_smtp(monkeypatch):
    FakeSMTP.instances = []
    FakeSMTP.fail_on_send = False
    monkeypatch.setattr(notifier.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(notifier, "SMTP_USERNAME", "sender@example.com")
    monkeypatch.setattr(notifier, "SMTP_PASSWORD", "not-a-real-password")
    monkeypatch.setattr(notifier, "NOTIFY_TO_EMAIL", "me@example.com")
    return FakeSMTP


def test_empty_list_sends_nothing(fake_smtp):
    assert notifier.send_new_postings_email([]) is True
    assert fake_smtp.instances == []


def test_missing_credentials_skip_sending(monkeypatch):
    monkeypatch.setattr(notifier, "SMTP_USERNAME", "")
    monkeypatch.setattr(notifier, "SMTP_PASSWORD", "")
    # no_network (conftest) would fail the test if a connection were opened
    assert notifier.send_new_postings_email(POSTINGS) is False


def test_sends_one_email_listing_every_posting(fake_smtp):
    assert notifier.send_new_postings_email(POSTINGS) is True

    [conn] = fake_smtp.instances
    assert conn.started_tls
    assert conn.logged_in_as == "sender@example.com"
    [(from_addr, to_addr, message)] = conn.sent
    assert (from_addr, to_addr) == ("sender@example.com", "me@example.com")
    assert "Subject: 2 new internship posting(s) found" in message
    assert "Software Engineering Intern @ examplegh (Remote)" in message
    assert "https://jobs.lever.co/examplelever/2" in message


def test_smtp_error_returns_false_instead_of_raising(fake_smtp):
    fake_smtp.fail_on_send = True
    assert notifier.send_new_postings_email(POSTINGS) is False
