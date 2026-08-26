from flask import Flask, render_template, request, redirect, url_for, jsonify

import config
from models import db, Posting
from tracker_job import run_tracker_job
from scheduler import start_scheduler

STATUS_OPTIONS = ["new", "applied", "interviewing", "rejected", "offer"]


def create_app():
    app = Flask(__name__)
    app.config.from_object(config)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.route("/")
    def index():
        status_filter = request.args.get("status", "")
        query = Posting.query
        if status_filter:
            query = query.filter_by(status=status_filter)
        postings = query.order_by(Posting.date_scraped.desc()).all()
        return render_template(
            "index.html",
            postings=postings,
            status_options=STATUS_OPTIONS,
            active_status=status_filter,
        )

    @app.route("/postings/<int:posting_id>/status", methods=["POST"])
    def update_status(posting_id):
        posting = Posting.query.get_or_404(posting_id)
        new_status = request.form.get("status")
        if new_status in STATUS_OPTIONS:
            posting.status = new_status
            db.session.commit()
        return redirect(url_for("index"))

    @app.route("/refresh", methods=["POST"])
    def refresh():
        result = run_tracker_job(app)
        return jsonify(result)

    return app


app = create_app()

if __name__ == "__main__":
    start_scheduler(app)
    app.run(debug=True)