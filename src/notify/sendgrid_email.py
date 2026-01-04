from __future__ import annotations
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_email(subject: str, html: str) -> None:
    api_key = os.getenv("SENDGRID_API_KEY")
    to_email = os.getenv("TO_EMAIL")
    from_email = os.getenv("FROM_EMAIL")

    missing = [k for k, v in {
        "SENDGRID_API_KEY": api_key,
        "TO_EMAIL": to_email,
        "FROM_EMAIL": from_email,
    }.items() if not v]
    if missing:
        raise RuntimeError(f"Missing env vars: {', '.join(missing)}")

    message = Mail(from_email=from_email, to_emails=to_email, subject=subject, html_content=html)
    SendGridAPIClient(api_key).send(message)
