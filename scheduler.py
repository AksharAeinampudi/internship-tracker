from apscheduler.schedulers.background import BackgroundScheduler

from config import SCRAPE_INTERVAL_HOURS
from tracker_job import run_tracker_job


def start_scheduler(app):
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(
        func=lambda: run_tracker_job(app),
        trigger="interval",
        hours=SCRAPE_INTERVAL_HOURS,
        id="tracker_job",
        replace_existing=True,
    )
    scheduler.start()
    return scheduler