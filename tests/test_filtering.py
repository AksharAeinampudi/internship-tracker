import pytest

import scraper
from scraper import matches_filters


def test_matches_filters_accepts_internship_in_title():
    posting = {"title": "Software Engineering Intern", "location": "Remote"}
    assert matches_filters(posting) is True


def test_matches_filters_rejects_unrelated_title():
    posting = {"title": "Senior Software Engineer", "location": "Remote"}
    assert matches_filters(posting) is False


def test_matches_filters_rejects_internal_as_false_positive():
    posting = {"title": "Internal Audit Lead", "location": "Remote"}
    assert matches_filters(posting) is False


def test_matches_filters_is_case_insensitive():
    posting = {"title": "SOFTWARE ENGINEERING INTERN", "location": "Remote"}
    assert matches_filters(posting) is True


@pytest.mark.parametrize(
    "title, expected",
    [
        ("Intern - Software Engineering", True),  # keyword at the start
        ("Software Engineer (Intern)", True),  # keyword next to punctuation
        ("Data Science Internship", True),  # the second keyword
        ("Software Engineering Intern, Summer 2027", True),
        ("International Sales Manager", False),  # "intern" inside a longer word
        ("Internals Engineer", False),
        ("Winternet Ops", False),  # "intern" in the middle of a word
        ("Internships Coordinator", False),  # plural is a different word
    ],
)
def test_matches_filters_uses_word_boundaries(title, expected):
    assert matches_filters({"title": title, "location": ""}) is expected


def test_location_keywords_narrow_the_matches(monkeypatch):
    monkeypatch.setattr(scraper, "LOCATION_KEYWORDS", ["remote", "new york"])
    assert matches_filters({"title": "Intern", "location": "Remote - US"}) is True
    assert matches_filters({"title": "Intern", "location": "New York, NY"}) is True
    assert matches_filters({"title": "Intern", "location": "Austin, TX"}) is False
    assert matches_filters({"title": "Intern", "location": None}) is False


def test_location_is_ignored_when_no_location_keywords(monkeypatch):
    monkeypatch.setattr(scraper, "LOCATION_KEYWORDS", [])
    assert matches_filters({"title": "Intern", "location": None}) is True