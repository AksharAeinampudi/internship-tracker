import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, NOTIFY_TO_EMAIL


def send_new_postings_email(postings: list[dict]) -> bool:
    if not postings:
        return True

    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print("[notifier] SMTP_USERNAME/SMTP_PASSWORD not set - skipping email")
        return False

    subject = f"{len(postings)} new internship posting(s) found"
    lines = [
        f"- {p['title']} @ {p['company']} ({p.get('location', 'n/a')})\n  {p['url']}"
        for p in postings
    ]
    body = "New postings matching your filters:\n\n" + "\n\n".join(lines)

    message = MIMEMultipart()
    message["From"] = SMTP_USERNAME
    message["To"] = NOTIFY_TO_EMAIL
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_USERNAME, NOTIFY_TO_EMAIL, message.as_string())
        print(f"[notifier] sent email for {len(postings)} posting(s)")
        return True
    except smtplib.SMTPException as exc:
        print(f"[notifier] failed to send email: {exc}")
        return False