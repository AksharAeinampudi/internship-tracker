from models import db, Posting
from scraper import fetch_all_matching_postings
from notifier import send_new_postings_email
from config import GREENHOUSE_COMPANY_SLUGS, LEVER_COMPANY_SLUGS


def run_tracker_job(app) -> dict:
    with app.app_context():
        matches = fetch_all_matching_postings(GREENHOUSE_COMPANY_SLUGS, LEVER_COMPANY_SLUGS)

        newly_added = []
        for match in matches:
            exists = Posting.query.filter_by(url=match["url"]).first()
            if exists:
                continue
            posting = Posting(
                company=match["company"],
                title=match["title"],
                location=match["location"],
                url=match["url"],
                date_posted=match["date_posted"],
            )
            db.session.add(posting)
            newly_added.append(posting)

        db.session.commit()

        if newly_added:
            sent = send_new_postings_email([p.to_dict() for p in newly_added])
            if sent:
                for p in newly_added:
                    p.notified = True
                db.session.commit()

        return {"scraped": len(matches), "new": len(newly_added)}