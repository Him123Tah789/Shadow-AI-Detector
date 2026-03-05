"""
Background Worker / Scheduler
==============================
Handles:
  1. Periodic breach checks (every 24h per monitored email)
  2. Event retention cleanup (delete usage_events > 30 days)
  3. 90-day security review reminders

Run: python worker.py
Requires: APScheduler, same DATABASE_URL as main app
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import (
    Base, MonitoredEmail, BreachEvent, BreachAlert,
    PersonalUser, UsageEvent, Reminder, SecurityScore,
)
from breach_service import get_breach_checker
from crypto_utils import decrypt_email
from notification_service import send_breach_email, send_reminder_email

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("worker")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://shadow_user:shadow_password@localhost/shadow_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


# ── Job 1: Periodic Breach Check ─────────────────

def run_breach_checks():
    """Check all active monitored emails for new breaches."""
    logger.info("Starting periodic breach check...")
    db = SessionLocal()

    try:
        emails = db.query(MonitoredEmail).filter(MonitoredEmail.is_active == True).all()
        checker = get_breach_checker()
        total_new = 0

        for me in emails:
            # Skip if checked within last 24h
            if me.last_checked and (datetime.utcnow() - me.last_checked).total_seconds() < 86400:
                continue

            try:
                raw_email = decrypt_email(me.email_encrypted)
                results = asyncio.get_event_loop().run_until_complete(checker.check(raw_email))

                for breach in results:
                    existing = db.query(BreachEvent).filter(
                        BreachEvent.monitored_email_id == me.id,
                        BreachEvent.source_name == breach.source_name,
                    ).first()
                    if not existing:
                        be = BreachEvent(
                            monitored_email_id=me.id,
                            source_name=breach.source_name,
                            breach_date=breach.breach_date,
                            data_classes=json.dumps(breach.data_classes),
                            severity=breach.severity,
                        )
                        db.add(be)
                        db.flush()
                        db.add(BreachAlert(
                            user_id=me.user_id,
                            breach_event_id=be.id,
                            channel="email",
                        ))
                        send_breach_email(
                            to_email=raw_email,
                            breach_source=breach.source_name,
                            breach_date=str(breach.breach_date) if breach.breach_date else None,
                            data_classes=breach.data_classes,
                        )
                        total_new += 1

                me.last_checked = datetime.utcnow()
                db.commit()

            except Exception as e:
                logger.error(f"Error checking email {me.id}: {e}")
                db.rollback()

        logger.info(f"Breach check complete. {total_new} new breach(es) found across {len(emails)} email(s).")

    finally:
        db.close()


# ── Job 2: Event Retention Cleanup ────────────────

def cleanup_old_events():
    """Delete usage_events older than 30 days (Module A retention)."""
    logger.info("Running event retention cleanup...")
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=30)
        deleted = db.query(UsageEvent).filter(UsageEvent.timestamp < cutoff).delete()
        db.commit()
        logger.info(f"Deleted {deleted} usage events older than 30 days.")
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        db.rollback()
    finally:
        db.close()


# ── Job 3: 90-Day Reminders ──────────────────────

def send_90day_reminders():
    """Send reminders to users who haven't had a security review in 90 days."""
    logger.info("Checking for 90-day reminder candidates...")
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=90)
        users = db.query(PersonalUser).all()

        for user in users:
            # Check if we already sent a reminder recently (within 80 days)
            recent_reminder = db.query(Reminder).filter(
                Reminder.user_id == user.id,
                Reminder.type == "90_day_review",
                Reminder.sent_at >= datetime.utcnow() - timedelta(days=80),
            ).first()
            if recent_reminder:
                continue

            # Check last score calculation
            last_score = db.query(SecurityScore).filter(
                SecurityScore.user_id == user.id,
            ).order_by(SecurityScore.calculated_at.desc()).first()

            if last_score and last_score.calculated_at < cutoff:
                # Time for a reminder
                message = (
                    f"It's been over 90 days since your last security review. "
                    f"Your last score was {last_score.score} ({last_score.grade}). "
                    f"Visit your dashboard to check for new breaches and update your recovery progress."
                )
                send_reminder_email(to_email=user.email, message=message)
                db.add(Reminder(
                    user_id=user.id,
                    type="90_day_review",
                    scheduled_for=datetime.utcnow(),
                    sent_at=datetime.utcnow(),
                    message=message,
                ))
                db.commit()
                logger.info(f"Sent 90-day reminder to user {user.id}")

    except Exception as e:
        logger.error(f"Reminder error: {e}")
        db.rollback()
    finally:
        db.close()


# ── Scheduler ────────────────────────────────────

if __name__ == "__main__":
    logger.info("Starting ShieldOps background worker...")
    logger.info(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}")

    scheduler = BlockingScheduler()

    # Run breach checks every 6 hours
    scheduler.add_job(run_breach_checks, "interval", hours=6, id="breach_check",
                      next_run_time=datetime.utcnow() + timedelta(seconds=30))

    # Cleanup old events daily at 3 AM UTC
    scheduler.add_job(cleanup_old_events, "cron", hour=3, id="event_cleanup")

    # Check for 90-day reminders daily at 10 AM UTC
    scheduler.add_job(send_90day_reminders, "cron", hour=10, id="reminders")

    logger.info("Scheduler started. Jobs: breach_check (6h), event_cleanup (3am), reminders (10am)")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Worker shutdown.")
