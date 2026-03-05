"""
Notification Service
====================
Email notifications via SMTP (SendGrid, Gmail, etc.)
Telegram bot notifications (stubbed for MVP — v1.1)

Config via env vars:
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM
  TELEGRAM_BOT_TOKEN (optional, for future use)
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)


# ── Email Notification ─────────────────────────────

def send_breach_email(
    to_email: str,
    breach_source: str,
    breach_date: Optional[str] = None,
    data_classes: Optional[list] = None,
    dashboard_url: str = "http://localhost:3000/personal/breaches",
) -> bool:
    """Send a breach notification email.

    Returns True if sent successfully, False otherwise.
    Falls back to logging if SMTP is not configured (MVP-friendly).
    """
    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    smtp_from = os.getenv("SMTP_FROM", "alerts@shieldops.app")

    subject = f"⚠️ Breach Alert: Your data was found in the {breach_source} breach"

    data_str = ", ".join(data_classes) if data_classes else "Unknown data types"
    date_str = breach_date or "Unknown date"

    html_body = f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #1e1b4b, #312e81); padding: 30px; border-radius: 12px; color: white; text-align: center;">
            <h1 style="margin: 0;">🛡️ ShieldOps</h1>
            <p style="opacity: 0.8;">Breach Monitor Alert</p>
        </div>

        <div style="padding: 20px;">
            <h2 style="color: #dc2626;">⚠️ Data Breach Detected</h2>

            <div style="background: #fef2f2; border-left: 4px solid #dc2626; padding: 16px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 0;"><strong>Source:</strong> {breach_source}</p>
                <p style="margin: 8px 0 0;"><strong>Breach Date:</strong> {date_str}</p>
                <p style="margin: 8px 0 0;"><strong>Exposed Data:</strong> {data_str}</p>
            </div>

            <p>Your email was found in a data breach. We recommend you take immediate action to secure your accounts.</p>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{dashboard_url}" style="background: #4f46e5; color: white; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: 600;">
                    Start Recovery →
                </a>
            </div>

            <p style="color: #6b7280; font-size: 14px;">
                ShieldOps never stores your passwords. We only track which recovery steps you've completed.
            </p>
        </div>

        <div style="border-top: 1px solid #e5e7eb; padding-top: 16px; text-align: center; color: #9ca3af; font-size: 12px;">
            <p>ShieldOps — Breach Monitor + Recovery Kit</p>
        </div>
    </body>
    </html>
    """

    if not smtp_host or not smtp_user:
        # No SMTP configured — log instead (MVP development mode)
        logger.info(f"[EMAIL STUB] Would send breach alert to {to_email}: {subject}")
        logger.info(f"[EMAIL STUB] Source={breach_source}, Date={date_str}, Data={data_str}")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = smtp_from
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_from, to_email, msg.as_string())

        logger.info(f"Breach alert sent to {to_email} for {breach_source}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


def send_reminder_email(
    to_email: str,
    message: str,
    dashboard_url: str = "http://localhost:3000/personal/score",
) -> bool:
    """Send a 90-day reminder email."""
    smtp_host = os.getenv("SMTP_HOST", "")

    if not smtp_host:
        logger.info(f"[EMAIL STUB] Reminder to {to_email}: {message}")
        return True

    # Simplified — same pattern as breach email
    subject = "🔒 ShieldOps: Time for your security review"
    html_body = f"""
    <html>
    <body style="font-family: -apple-system, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #1e1b4b, #312e81); padding: 30px; border-radius: 12px; color: white; text-align: center;">
            <h1 style="margin: 0;">🛡️ ShieldOps</h1>
            <p style="opacity: 0.8;">Security Reminder</p>
        </div>
        <div style="padding: 20px;">
            <h2>⏰ Time for a Security Check-Up</h2>
            <p>{message}</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{dashboard_url}" style="background: #4f46e5; color: white; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: 600;">
                    View Security Score →
                </a>
            </div>
        </div>
    </body>
    </html>
    """

    try:
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        smtp_from = os.getenv("SMTP_FROM", "alerts@shieldops.app")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = smtp_from
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_from, to_email, msg.as_string())

        return True
    except Exception as e:
        logger.error(f"Failed to send reminder to {to_email}: {e}")
        return False


# ── Telegram Notification (Stub for v1.1) ─────────

def send_telegram_alert(chat_id: str, message: str) -> bool:
    """Send a Telegram message. Stubbed for MVP — implement in v1.1."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not bot_token:
        logger.info(f"[TELEGRAM STUB] Would send to chat {chat_id}: {message}")
        return True

    # TODO v1.1: Implement Telegram Bot API call
    # import httpx
    # resp = httpx.post(f"https://api.telegram.org/bot{bot_token}/sendMessage",
    #     json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"})
    # return resp.status_code == 200
    logger.info(f"[TELEGRAM STUB] Would send to chat {chat_id}: {message}")
    return True
