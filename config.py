import os
from dotenv import load_dotenv

load_dotenv()


def normalize_database_url(url: str) -> str:
    """Point Postgres URLs at the psycopg 3 driver.

    Hosts such as Neon and Render hand out URLs starting with ``postgres://`` or
    ``postgresql://``. SQLAlchemy reads those as "use psycopg2", which isn't installed,
    so rewrite them to ``postgresql+psycopg://``. Other URLs (SQLite) pass through.
    """
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix) :]
    return url


# --- Database ---
SQLALCHEMY_DATABASE_URI = normalize_database_url(
    os.environ.get("DATABASE_URL") or "sqlite:///internships.db"
)
SQLALCHEMY_TRACK_MODIFICATIONS = False
# Hosted Postgres (e.g. Neon) closes idle connections; test each one before using it.
SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

# --- Companies to scrape ---
GREENHOUSE_COMPANY_SLUGS = [
    "stripe",
    "airbnb",
    "robinhood",
]
LEVER_COMPANY_SLUGS = [
    "traackr",
]

# --- Filtering ---
TITLE_KEYWORDS = ["intern", "internship"]
LOCATION_KEYWORDS = []

# --- Email notifications ---
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
NOTIFY_TO_EMAIL = os.environ.get("NOTIFY_TO_EMAIL", SMTP_USERNAME)

# --- Scheduler ---
SCRAPE_INTERVAL_HOURS = int(os.environ.get("SCRAPE_INTERVAL_HOURS", 6))