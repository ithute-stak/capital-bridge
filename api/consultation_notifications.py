"""Opt-in, at-least-once consultation notification email worker.

Run with a separately provisioned least-privilege worker DB account.
A crash after SMTP send but before database commit can cause a duplicate;
receivers must tolerate at-least-once delivery.
"""
from __future__ import annotations

import os
import smtplib
import ssl
from email.message import EmailMessage

import psycopg
from psycopg.rows import dict_row


def send_staff_notice(*, event_id, service: str, name: str) -> None:
    host = os.environ["CB_NOTIFY_SMTP_HOST"]
    sender = os.environ["CB_NOTIFY_FROM"]
    recipient = os.environ["CB_NOTIFY_STAFF_TO"]
    username = os.environ["CB_NOTIFY_SMTP_USER"]
    password = os.environ["CB_NOTIFY_SMTP_PASSWORD"]
    if not host or not sender or not recipient or not username or not password:
        raise RuntimeError("Notification SMTP configuration incomplete")
    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = "CapitalBridge consultation enquiry received"
    message["Message-ID"] = "<" + str(event_id) + "@capitalbridge.co.ls>"
    message.set_content(
        "A consultation enquiry requires staff review.\n\n"
        "Service: " + service + "\n"
        "Client: " + name + "\n\n"
        "Log in to CapitalBridge ONE to review the enquiry securely.\n"
        "Do not send customer documents in reply to this automated notice."
    )
    context = ssl.create_default_context()
    with smtplib.SMTP(host, 587, timeout=15) as smtp:
        smtp.starttls(context=context)
        smtp.login(username, password)
        smtp.send_message(message)


def deliver_one() -> bool:
    """Deliver one pending event with a row lock; mark sent only after SMTP success."""
    dsn = os.environ["CB_CONSULTATION_NOTIFY_DSN"]
    if not dsn:
        raise RuntimeError("Notification worker DSN missing")
    with psycopg.connect(dsn, row_factory=dict_row, autocommit=False) as db:
        with db.transaction():
            event = db.execute(
                """SELECT o.id,o.company_id,o.enquiry_id,e.service,e.contact_name
                   FROM cb.consultation_notification_outbox o
                   JOIN cb.consultation_enquiries e ON
                     e.company_id=o.company_id AND e.id=o.enquiry_id
                   WHERE o.sent_at IS NULL AND o.event_type='consultation.received'
                   ORDER BY o.created_at,o.id
                   LIMIT 1 FOR UPDATE OF o SKIP LOCKED"""
            ).fetchone()
            if event is None:
                return False
            db.execute(
                """UPDATE cb.consultation_notification_outbox
                   SET attempts=attempts+1 WHERE id=%s""", (event["id"],)
            )
            send_staff_notice(event_id=event["id"],
                              service=event["service"],name=event["contact_name"])
            db.execute(
                """UPDATE cb.consultation_notification_outbox
                   SET sent_at=now() WHERE id=%s""", (event["id"],)
            )
    return True


if __name__ == "__main__":
    deliver_one()
