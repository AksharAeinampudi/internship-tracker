import os
from dotenv import load_dotenv

load_dotenv()

# --- Database ---
SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///internships.db")
SQLALCHEMY_TRACK_MODIFICATIONS = False

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