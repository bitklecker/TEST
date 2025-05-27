import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_summary_email(created, updated):
    sender = os.getenv("EMAIL_SENDER")
    receiver = os.getenv("EMAIL_RECEIVER")
    password = os.getenv("EMAIL_APP_PASSWORD")

    subject = "📝 Jira → Notion Sync Summary"
    body = ""

    if created:
        body += f"➕ Created {len(created)} tickets:\n" + "\n".join(created.keys()) + "\n\n"
    if updated:
        body += f"🔄 Updated {len(updated)} tickets:\n" + "\n".join(updated.keys()) + "\n\n"
    if not body:
        body = "No ticket changes in this cycle."

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
