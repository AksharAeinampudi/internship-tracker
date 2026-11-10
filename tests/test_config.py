import pytest

from config import normalize_database_url


@pytest.mark.parametrize(
    "url, expected",
    [
        # Render and Heroku style
        ("postgres://u:p@host:5432/db", "postgresql+psycopg://u:p@host:5432/db"),
        # Neon style, query string kept as is
        (
            "postgresql://u:p@ep-x.us-east-2.aws.neon.tech/db?sslmode=require",
            "postgresql+psycopg://u:p@ep-x.us-east-2.aws.neon.tech/db?sslmode=require",
        ),
        # already explicit, or not Postgres: unchanged
        ("postgresql+psycopg://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
        ("sqlite:///internships.db", "sqlite:///internships.db"),
    ],
)
def test_normalize_database_url(url, expected):
    assert normalize_database_url(url) == expected
