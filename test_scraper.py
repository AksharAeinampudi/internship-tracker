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