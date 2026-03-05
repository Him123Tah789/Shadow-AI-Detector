from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


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
    action_taken = Column(String, nullable=False)      # allow | warn | block
    timestamp = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_events_org_ts", "org_id", "timestamp"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=False)
    action = Column(String, nullable=False)
    detail = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    admin = relationship("Admin")
