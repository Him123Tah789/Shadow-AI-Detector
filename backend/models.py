from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


# ══════════════════════════════════════════════════
#  MODULE A — Shadow AI Detector (Org / B2B)
# ══════════════════════════════════════════════════


class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    admins = relationship("Admin", back_populates="org")
    policies = relationship("Policy", back_populates="org")


class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="admin")  # admin | viewer

    org = relationship("Organization", back_populates="admins")


class ToolCatalog(Base):
    __tablename__ = "tools_catalog"
    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)          # chat | code | image | file
    base_risk_score = Column(Integer, default=5)       # 1-10


class Policy(Base):
    __tablename__ = "policies"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    tool_id = Column(Integer, ForeignKey("tools_catalog.id"), nullable=False)
    action = Column(String, default="warn")            # allow | warn | block
    alternative_tool_id = Column(Integer, ForeignKey("tools_catalog.id"), nullable=True)

    org = relationship("Organization", back_populates="policies")
    tool = relationship("ToolCatalog", foreign_keys=[tool_id])
    alternative = relationship("ToolCatalog", foreign_keys=[alternative_tool_id])

    __table_args__ = (
        Index("ix_policy_org_tool", "org_id", "tool_id", unique=True),
    )


class UsageEvent(Base):
    __tablename__ = "usage_events"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    domain = Column(String, nullable=False)
    user_hash = Column(String, nullable=False)
    policy_action = Column(String, nullable=False)      # allow | warn | block
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # New real-life fields
    event_type = Column(String, default="shadow_ai.access", nullable=False)
    risk_score = Column(Integer, nullable=True)        # 1-10
    device_hash = Column(String, nullable=True)        # Anonymous stable hash
    tool_name = Column(String, nullable=True)          # ChatGPT
    category = Column(String, nullable=True)           # Chat | Code | Image | File
    policy_rule_id = Column(Integer, ForeignKey("policies.id"), nullable=True)
    browser = Column(String, nullable=True)            # Chrome 116.0
    extension_version = Column(String, nullable=True)  # 1.0.0
    ip_site = Column(String, nullable=True)            # office/site id
    geo_region = Column(String, nullable=True)         # e.g. Dhaka (coarse)

    __table_args__ = (
        Index("ix_events_org_ts", "org_id", "timestamp"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=False)
    action = Column(String, nullable=False)
    rule_before = Column(String, nullable=True)
    rule_after = Column(String, nullable=True)
    reason = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # New real-life fields
    event_type = Column(String, default="shadow_ai.policy_change", nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    admin = relationship("Admin")


class AlertEvent(Base):
    """Alert logic for anomalies like spike usage, high-risk access."""
    __tablename__ = "alert_events"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    alert_type = Column(String, nullable=False)        # SpikeUsage | HighRiskToolAccess | NewToolSeen
    severity = Column(String, nullable=False)          # Low | Med | High
    domain = Column(String, nullable=False)
    count_threshold = Column(Integer, nullable=True)   # E.g. 21 (for spike)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # New real-life fields
    event_type = Column(String, default="shadow_ai.alert", nullable=False)
    unique_users = Column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_alerts_org_ts", "org_id", "timestamp"),
    )


class DashboardLog(Base):
    """Track dashboard visitors non-content tracking."""
    __tablename__ = "dashboard_logs"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=True)
    page_visited = Column(String, nullable=False)      # /overview, /policies
    session_id = Column(String, nullable=True)
    device_info = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_dashlogs_org_ts", "org_id", "timestamp"),
    )


# ══════════════════════════════════════════════════
#  MODULE B — Breach Monitor + Recovery Kit (Personal)
# ══════════════════════════════════════════════════


class PersonalUser(Base):
    """Individual user for breach monitoring — separate from org admins."""
    __tablename__ = "personal_users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    tier = Column(String, default="free")              # free | pro | family
    max_emails = Column(Integer, default=1)            # free=1, pro=5, family=10
    telegram_chat_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    monitored_emails = relationship("MonitoredEmail", back_populates="user", cascade="all, delete-orphan")
    recovery_plans = relationship("RecoveryPlan", back_populates="user", cascade="all, delete-orphan")
    security_scores = relationship("SecurityScore", back_populates="user", cascade="all, delete-orphan")


class MonitoredEmail(Base):
    """Emails being watched for breaches. Email stored encrypted, hash for lookups."""
    __tablename__ = "monitored_emails"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("personal_users.id"), nullable=False)
    email_encrypted = Column(String, nullable=False)   # AES-256 encrypted
    email_hash = Column(String, nullable=False, index=True)  # SHA-256 for dedup
    label = Column(String, nullable=True)              # "Work email"
    is_active = Column(Boolean, default=True)
    added_at = Column(DateTime, default=datetime.utcnow)
    last_checked = Column(DateTime, nullable=True)

    user = relationship("PersonalUser", back_populates="monitored_emails")
    breach_events = relationship("BreachEvent", back_populates="monitored_email", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_monitored_user", "user_id"),
    )


class BreachEvent(Base):
    """Individual breach records per monitored email."""
    __tablename__ = "breach_events"
    id = Column(Integer, primary_key=True, index=True)
    monitored_email_id = Column(Integer, ForeignKey("monitored_emails.id"), nullable=False)
    source_name = Column(String, nullable=False)       # "LinkedIn", "Adobe"
    breach_date = Column(Date, nullable=True)
    data_classes = Column(Text, nullable=True)         # JSON: ["Emails","Passwords"]
    severity = Column(String, default="medium")        # low | medium | high | critical
    discovered_at = Column(DateTime, default=datetime.utcnow)

    monitored_email = relationship("MonitoredEmail", back_populates="breach_events")
    alerts = relationship("BreachAlert", back_populates="breach_event", cascade="all, delete-orphan")
    recovery_plans = relationship("RecoveryPlan", back_populates="breach_event", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_breach_email", "monitored_email_id"),
        Index("ix_breach_email_source", "monitored_email_id", "source_name", unique=True),
    )


class BreachAlert(Base):
    """Notifications sent to user about breaches."""
    __tablename__ = "breach_alerts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("personal_users.id"), nullable=False)
    breach_event_id = Column(Integer, ForeignKey("breach_events.id"), nullable=False)
    channel = Column(String, nullable=False)           # email | telegram
    sent_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)

    breach_event = relationship("BreachEvent")

    __table_args__ = (
        Index("ix_alerts_user", "user_id", "sent_at"),
    )


class RecoveryPlan(Base):
    """Per-platform recovery checklists."""
    __tablename__ = "recovery_plans"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("personal_users.id"), nullable=False)
    breach_event_id = Column(Integer, ForeignKey("breach_events.id"), nullable=True)
    platform = Column(String, nullable=False)          # google | facebook | github ...
    status = Column(String, default="pending")         # pending | in_progress | completed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("PersonalUser", back_populates="recovery_plans")
    breach_event = relationship("BreachEvent")
    tasks = relationship("RecoveryTask", back_populates="plan", cascade="all, delete-orphan",
                         order_by="RecoveryTask.sort_order")

    __table_args__ = (
        Index("ix_recovery_user", "user_id"),
    )


class RecoveryTask(Base):
    """Individual checklist items within a recovery plan."""
    __tablename__ = "recovery_tasks"
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("recovery_plans.id"), nullable=False)
    task_key = Column(String, nullable=False)          # change_password | enable_2fa ...
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    help_url = Column(String, nullable=True)           # Direct link to platform settings
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    sort_order = Column(Integer, default=0)

    plan = relationship("RecoveryPlan", back_populates="tasks")

    __table_args__ = (
        Index("ix_tasks_plan", "plan_id"),
    )


class SecurityScore(Base):
    """Periodic security score snapshots per user."""
    __tablename__ = "security_scores"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("personal_users.id"), nullable=False)
    score = Column(Integer, nullable=False)            # 0-100
    grade = Column(String, nullable=False)             # A | B | C | D | F
    breakdown = Column(Text, nullable=True)            # JSON details
    calculated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("PersonalUser", back_populates="security_scores")

    __table_args__ = (
        Index("ix_scores_user", "user_id", "calculated_at"),
    )


class Reminder(Base):
    """Scheduled reminders for periodic security reviews."""
    __tablename__ = "reminders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("personal_users.id"), nullable=False)
    type = Column(String, nullable=False)              # 90_day_review | incomplete_task
    scheduled_for = Column(DateTime, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    message = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_reminders_sched", "scheduled_for", "sent_at"),
    )
