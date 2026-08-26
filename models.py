from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Posting(db.Model):
    __tablename__ = "postings"

    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255))
    url = db.Column(db.String(500), unique=True, nullable=False)
    date_posted = db.Column(db.String(50))
    date_scraped = db.Column(db.DateTime, default=datetime.utcnow)

    status = db.Column(db.String(30), default="new")
    notified = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "company": self.company,
            "title": self.title,
            "location": self.location,
            "url": self.url,
            "date_posted": self.date_posted,
            "date_scraped": self.date_scraped.isoformat() if self.date_scraped else None,
            "status": self.status,
        }