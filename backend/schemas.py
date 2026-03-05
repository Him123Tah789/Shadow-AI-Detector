from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ── Auth ──────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    org_name: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    org_id: int
    org_token: str


# ── Events ────────────────────────────────────────
class EventCreate(BaseModel):
    domain: str
    user_hash: str
    action_taken: str  # "allow" | "warn" | "block"
    timestamp: datetime

class EventOut(BaseModel):
    id: int
    domain: str
    user_hash: str
    action_taken: str
    timestamp: datetime
    class Config:
        from_attributes = True


# ── Policy ────────────────────────────────────────
class PolicyItem(BaseModel):
    tool_id: int
    action: str  # "allow" | "warn" | "block"
    alternative_tool_id: Optional[int] = None

class PolicyOut(BaseModel):
    id: int
    tool_id: int
    tool_name: Optional[str] = None
    tool_domain: Optional[str] = None
    action: str
    alternative_tool_id: Optional[int] = None
    alternative_name: Optional[str] = None
    class Config:
        from_attributes = True

class PolicySyncOut(BaseModel):
    """Flat map returned to the extension for local caching"""
    policies: dict  # { "domain": { "action": "warn", "alternative": "..." } }


# ── Tools Catalog ─────────────────────────────────
class ToolOut(BaseModel):
    id: int
    domain: str
    name: str
    category: str
    base_risk_score: int
    class Config:
        from_attributes = True


# ── Analytics ─────────────────────────────────────
class TopToolItem(BaseModel):
    name: str
    domain: str
    category: str
    count: int

class TrendPoint(BaseModel):
    date: str
    count: int

class RiskScoreOut(BaseModel):
    category: str
    score: float
    event_count: int


# ── Audit ─────────────────────────────────────────
class AuditLogOut(BaseModel):
    id: int
    admin_email: str
    action: str
    detail: Optional[str] = None
    timestamp: datetime
    class Config:
        from_attributes = True
