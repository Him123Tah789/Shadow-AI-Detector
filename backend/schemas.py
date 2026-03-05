from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ══════════════════════════════════════════════════
#  AUTH (Module A — Org)
# ══════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════
#  AUTH (Module B — Personal)
# ══════════════════════════════════════════════════

class PersonalRegisterRequest(BaseModel):
    email: str
    password: str

class PersonalLoginRequest(BaseModel):
    email: str
    password: str

class PersonalTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    tier: str
    max_emails: int


# ══════════════════════════════════════════════════
#  EVENTS (Module A)
# ══════════════════════════════════════════════════

class EventCreate(BaseModel):
    domain: str
    user_hash: str
    policy_action: str  # "allow" | "warn" | "block"
    timestamp: datetime
    
    # New real-life fields
    event_type: str = "shadow_ai.access"
    risk_score: Optional[int] = None
    device_hash: Optional[str] = None
    tool_name: Optional[str] = None
    category: Optional[str] = None
    policy_rule_id: Optional[int] = None
    browser: Optional[str] = None
    extension_version: Optional[str] = None
    ip_site: Optional[str] = None
    geo_region: Optional[str] = None

class EventOut(BaseModel):
    id: int
    domain: str
    user_hash: str
    policy_action: str
    timestamp: datetime
    
    # New real-life fields
    event_type: str
    risk_score: Optional[int] = None
    device_hash: Optional[str] = None
    tool_name: Optional[str] = None
    category: Optional[str] = None
    policy_rule_id: Optional[int] = None
    browser: Optional[str] = None
    extension_version: Optional[str] = None
    ip_site: Optional[str] = None
    geo_region: Optional[str] = None

    class Config:
        from_attributes = True


# ══════════════════════════════════════════════════
#  POLICY (Module A)
# ══════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════
#  TOOLS CATALOG (Module A)
# ══════════════════════════════════════════════════

class ToolOut(BaseModel):
    id: int
    domain: str
    name: str
    category: str
    base_risk_score: int
    class Config:
        from_attributes = True


# ══════════════════════════════════════════════════
#  ANALYTICS (Module A)
# ══════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════
#  AUDIT (Module A)
# ══════════════════════════════════════════════════

class AuditLogOut(BaseModel):
    id: int
    admin_email: str
    action: str
    rule_before: Optional[str] = None
    rule_after: Optional[str] = None
    reason: Optional[str] = None
    timestamp: datetime
    
    # New real-life fields
    event_type: str = "shadow_ai.policy_change"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    class Config:
        from_attributes = True

class AlertOut(BaseModel):
    id: int
    org_id: int
    alert_type: str
    severity: str
    domain: str
    count_threshold: Optional[int] = None
    timestamp: datetime
    
    # New real-life fields
    event_type: str = "shadow_ai.alert"
    unique_users: Optional[int] = None

    class Config:
        from_attributes = True

class DashboardLogCreate(BaseModel):
    page_visited: str
    session_id: Optional[str] = None
    device_info: Optional[str] = None

class DashboardLogOut(BaseModel):
    id: int
    org_id: Optional[int] = None
    admin_id: Optional[int] = None
    page_visited: str
    session_id: Optional[str] = None
    device_info: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


# ══════════════════════════════════════════════════
#  BREACH MONITOR (Module B)
# ══════════════════════════════════════════════════

class MonitorEmailRequest(BaseModel):
    email: str
    label: Optional[str] = None

class MonitoredEmailOut(BaseModel):
    id: int
    email_masked: str
    label: Optional[str] = None
    is_active: bool
    added_at: datetime
    last_checked: Optional[datetime] = None
    breach_count: int = 0

class BreachEventOut(BaseModel):
    id: int
    source_name: str
    breach_date: Optional[str] = None
    data_classes: Optional[List[str]] = None
    severity: str
    discovered_at: datetime

class BreachStatusOut(BaseModel):
    monitored_emails: List[dict]
    total_breaches: int
    unresolved: int

class RunCheckRequest(BaseModel):
    monitored_email_id: int

class RunCheckResponse(BaseModel):
    status: str
    message: str
    new_breaches: int = 0


# ══════════════════════════════════════════════════
#  RECOVERY KIT (Module B)
# ══════════════════════════════════════════════════

class CreateRecoveryPlanRequest(BaseModel):
    platform: str
    breach_event_id: Optional[int] = None

class RecoveryTaskOut(BaseModel):
    id: int
    task_key: str
    title: str
    description: Optional[str] = None
    help_url: Optional[str] = None
    is_completed: bool
    completed_at: Optional[datetime] = None
    sort_order: int
    class Config:
        from_attributes = True

class RecoveryPlanOut(BaseModel):
    id: int
    platform: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    tasks: List[RecoveryTaskOut] = []
    progress: float = 0.0  # 0.0 – 1.0

class UpdateTaskRequest(BaseModel):
    is_completed: bool


# ══════════════════════════════════════════════════
#  SECURITY SCORE (Module B)
# ══════════════════════════════════════════════════

class SecurityScoreOut(BaseModel):
    score: int
    grade: str
    breakdown: dict
    recommendations: List[str] = []

class ScoreHistoryPoint(BaseModel):
    score: int
    grade: str
    calculated_at: datetime
