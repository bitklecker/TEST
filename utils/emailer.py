import os
import smtplib
import logging
from datetime import datetime
import pytz
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_summary_email(created, updated):
    sender = os.getenv("EMAIL_SENDER")
    receiver = os.getenv("EMAIL_RECEIVER")
    password = os.getenv("EMAIL_APP_PASSWORD")
    jira_domain = os.getenv("JIRA_DOMAIN")

    # Format timestamp in ET
    now = datetime.now(pytz.timezone("America/New_York"))
    timestamp = now.strftime("%A, %B %d at %I:%M %p ET")

    subject = "📝 Jira → Notion Sync Summary"
    body = f"📅 {timestamp}\n\n"

    if created:
        body += f"✅ Created {len(created)} tickets:\n"
        for key, meta in created.items():
            summary = meta.get("summary", "No summary")
            link = f"https://{jira_domain}/browse/{key}"
            body += f"- [{key}]({link}): {summary}\n"
        body += "\n"

    if updated:
        body += f"🔄 Updated {len(updated)} tickets:\n"
        for key, changes in updated.items():
            link = f"https://{jira_domain}/browse/{key}"
            body += f"- [{key}]({link})\n"
            for field, change in changes.items():
                if field in ("created", "link"):
                    continue
                before = change.get("before", "")
                after = change.get("after", "")
                body += f"  • {field}: {before} → {after}\n"
        body += "\n"

    if not created and not updated:
        body += "No ticket changes in this cycle.\n"

    # Email setup
    message = MIMEMultipart()
    message["From"] = sender
    message["To"] = receiver
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.send_message(message)
        logging.info(f"📧 Email summary sent to {receiver}")
    except Exception as e:
        logging.error(f"❌ Failed to send summary email: {e}")

def send_error_email(subject, error_text):
    sender = os.getenv("EMAIL_SENDER")
    receiver = os.getenv("EMAIL_RECEIVER")
    password = os.getenv("EMAIL_APP_PASSWORD")

    message = MIMEMultipart()
    message["From"] = sender
    message["To"] = receiver
    message["Subject"] = subject
    message.attach(MIMEText(error_text, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.send_message(message)
        logging.info(f"📧 Error email sent to {receiver}")
    except Exception as e:
        logging.error(f"❌ Failed to send error email: {e}")
