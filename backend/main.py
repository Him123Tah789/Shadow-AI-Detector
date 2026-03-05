"""
Shadow AI Detector + Breach Monitor – FastAPI Backend
======================================================
Module A: Privacy-first Shadow AI tool detection (domain-level only)
Module B: Account breach monitoring + recovery kit

Privacy: Only domain/timestamp/org_id/user_hash stored (Module A).
         Emails encrypted at rest (Module B). NO passwords ever stored.
"""

import asyncio
import json
import secrets
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import engine, get_db
from models import (
    Base, Organization, Admin, ToolCatalog, Policy, UsageEvent, AuditLog, AlertEvent,
    PersonalUser, MonitoredEmail, BreachEvent, BreachAlert,
    RecoveryPlan, RecoveryTask, SecurityScore,
)
from schemas import (
    LoginRequest, RegisterRequest, TokenResponse,
    PersonalRegisterRequest, PersonalLoginRequest, PersonalTokenResponse,
    EventCreate, EventOut,
    PolicyItem, PolicyOut, PolicySyncOut,
    ToolOut, TopToolItem, TrendPoint, RiskScoreOut,
    AuditLogOut, AlertOut,
    MonitorEmailRequest, MonitoredEmailOut, BreachEventOut,
    BreachStatusOut, RunCheckRequest, RunCheckResponse,
    CreateRecoveryPlanRequest, RecoveryPlanOut, RecoveryTaskOut,
    UpdateTaskRequest,
    SecurityScoreOut, ScoreHistoryPoint,
)
from auth import (
    hash_password, verify_password,
    create_access_token, get_current_user, require_admin,
    decode_token,
)
from seed import seed_tools
from crypto_utils import encrypt_email, decrypt_email, hash_email, mask_email
from breach_service import get_breach_checker
from recovery_templates import get_recovery_template, get_supported_platforms
from notification_service import send_breach_email

# ── App setup ─────────────────────────────────────
app = FastAPI(title="ShieldOps API", version="2.0.0",
              description="Shadow AI Detector (B2B) + Breach Monitor (B2C)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    seed_tools(db)
    db.close()


# ══════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════

def _get_org_by_token(org_token: str, db: Session) -> Organization:
    org = db.query(Organization).filter(Organization.token == org_token).first()
    if not org:
        raise HTTPException(401, "Invalid org token")
    return org


def _get_personal_user(credentials, db: Session) -> PersonalUser:
    """Extract personal user from JWT token."""
    payload = credentials
    user_id = payload.get("personal_user_id")
    if not user_id:
        raise HTTPException(403, "Personal user access required")
    user = db.query(PersonalUser).get(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user


# ══════════════════════════════════════════════════════════════════
#                          MODULE A
#           Shadow AI Detector (B2B / Org Endpoints)
# ══════════════════════════════════════════════════════════════════


# ── AUTH (Org) ────────────────────────────────────

@app.post("/api/v1/auth/register", response_model=TokenResponse, tags=["Auth – Org"])
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(Admin).filter(Admin.email == body.email).first():
        raise HTTPException(400, "Email already registered")
    org = Organization(name=body.org_name, token=secrets.token_urlsafe(32))
    db.add(org)
    db.flush()
    admin = Admin(
        org_id=org.id,
        email=body.email,
        password_hash=hash_password(body.password),
        role="admin",
    )
    db.add(admin)
    db.commit()
    db.refresh(org)
    db.refresh(admin)
    token = create_access_token({"sub": admin.email, "org_id": org.id, "role": admin.role})
    return TokenResponse(access_token=token, role=admin.role, org_id=org.id, org_token=org.token)


@app.post("/api/v1/auth/login", response_model=TokenResponse, tags=["Auth – Org"])
def login(body: LoginRequest, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.email == body.email).first()
    if not admin or not verify_password(body.password, admin.password_hash):
        raise HTTPException(401, "Invalid credentials")
    org = db.query(Organization).get(admin.org_id)
    token = create_access_token({"sub": admin.email, "org_id": org.id, "role": admin.role})
    return TokenResponse(access_token=token, role=admin.role, org_id=org.id, org_token=org.token)


# ── EXTENSION ENDPOINTS ──────────────────────────

@app.post("/api/v1/events", status_code=201, tags=["Extension"])
def record_event(event: EventCreate, db: Session = Depends(get_db), org_token: str = Header(None)):
    org = _get_org_by_token(org_token, db)
    if abs((datetime.utcnow() - event.timestamp).total_seconds()) > 86400:
        raise HTTPException(400, "Timestamp out of range")
    
    # Check if tool is known for category mapping
    tool = db.query(ToolCatalog).filter(ToolCatalog.domain == event.domain).first()
    category = tool.category if tool else (event.category or "unknown")
    tool_name = tool.name if tool else (event.tool_name or "unknown")

    row = UsageEvent(
        org_id=org.id, domain=event.domain,
        user_hash=event.user_hash, policy_action=event.policy_action,
        timestamp=event.timestamp,
        device_hash=event.device_hash,
        tool_name=tool_name,
        category=category,
        policy_rule_id=event.policy_rule_id,
        browser=event.browser,
        extension_version=event.extension_version,
        ip_site=event.ip_site,
        geo_region=event.geo_region,
    )
    db.add(row)

    # --- Real-Life ALERTS Logic ---
    # 1. High Risk Alert
    if tool and tool.base_risk_score > 7:
        db.add(AlertEvent(
            org_id=org.id,
            alert_type="HighRiskToolAccess",
            severity="High",
            domain=event.domain,
            timestamp=datetime.utcnow(),
        ))
        
    # 2. Spike Usage Alert
    ten_mins_ago = datetime.utcnow() - timedelta(minutes=10)
    hit_count = db.query(func.count(UsageEvent.id)).filter(
        UsageEvent.org_id == org.id,
        UsageEvent.user_hash == event.user_hash,
        UsageEvent.timestamp >= ten_mins_ago
    ).scalar() or 0
    
    # Event hasn't been committed yet, so we add 1
    if hit_count >= 19: # Trigger if 20th or more
        db.add(AlertEvent(
            org_id=org.id,
            alert_type="SpikeUsage",
            severity="Medium",
            domain=event.domain,
            count_threshold=20,
            unique_users=1,
            timestamp=datetime.utcnow(),
        ))
        
    # 3. New Tool Seen Alert
    if not tool:
        db.add(AlertEvent(
            org_id=org.id,
            alert_type="NewToolSeen",
            severity="Low",
            domain=event.domain,
            timestamp=datetime.utcnow(),
        ))

    db.commit()
    return {"status": "recorded"}


@app.post("/api/v1/events/batch", status_code=201, tags=["Extension"])
def record_events_batch(events: List[EventCreate], db: Session = Depends(get_db), org_token: str = Header(None)):
    org = _get_org_by_token(org_token, db)
    now = datetime.utcnow()
    rows = []
    alerts = []
    
    # Cache tools to avoid repeated DB lookups
    tools_cache = {t.domain: t for t in db.query(ToolCatalog).all()}
    
    # Track spike usage in memory for the batch
    user_hits = {}

    for e in events:
        if abs((now - e.timestamp).total_seconds()) > 86400:
            continue
            
        tool = tools_cache.get(e.domain)
        category = tool.category if tool else (e.category or "unknown")
        tool_name = tool.name if tool else (e.tool_name or "unknown")
        
        rows.append(UsageEvent(
            org_id=org.id, domain=e.domain,
            user_hash=e.user_hash, policy_action=e.policy_action,
            timestamp=e.timestamp,
            device_hash=e.device_hash,
            tool_name=tool_name,
            category=category,
            policy_rule_id=e.policy_rule_id,
            browser=e.browser,
            extension_version=e.extension_version,
            ip_site=e.ip_site,
            geo_region=e.geo_region,
        ))
        
        # --- Real-Life ALERTS Logic ---
        # 1. High Risk Alert
        if tool and tool.base_risk_score > 7:
            alerts.append(AlertEvent(
                org_id=org.id,
                alert_type="HighRiskToolAccess",
                severity="High",
                domain=e.domain,
                timestamp=now,
            ))

        # 3. New Tool Seen Alert (per-event check)
        if not tool:
            alerts.append(AlertEvent(
                org_id=org.id,
                alert_type="NewToolSeen",
                severity="Low",
                domain=e.domain,
                timestamp=now,
            ))
            
        # 2. Spike Usage Alert
        # Count hits in batch (real robust system would query DB + batch sum)
        user_hits[e.user_hash] = user_hits.get(e.user_hash, 0) + 1

    # Check for spikes in this batch alone
    for usr, cnt in user_hits.items():
        if cnt >= 20:
             alerts.append(AlertEvent(
                org_id=org.id,
                alert_type="SpikeUsage",
                severity="Medium",
                domain="multiple",
                count_threshold=20,
                unique_users=1,
                timestamp=now,
            ))

    db.add_all(rows)
    db.add_all(alerts)
    db.commit()
    return {"status": "recorded", "count": len(rows)}


@app.get("/api/v1/policy/sync", response_model=PolicySyncOut, tags=["Extension"])
def sync_policy(db: Session = Depends(get_db), org_token: str = Header(None)):
    org = _get_org_by_token(org_token, db)
    policies = (
        db.query(Policy, ToolCatalog)
        .join(ToolCatalog, Policy.tool_id == ToolCatalog.id)
        .filter(Policy.org_id == org.id)
        .all()
    )
    out: dict = {}
    for pol, tool in policies:
        alt_name = None
        if pol.alternative_tool_id:
            alt = db.query(ToolCatalog).get(pol.alternative_tool_id)
            alt_name = alt.domain if alt else None
        out[tool.domain] = {"action": pol.action, "alternative": alt_name, "rule_id": pol.id}
    return PolicySyncOut(policies=out)


# ── TOOLS CATALOG ─────────────────────────────────

@app.get("/api/v1/tools", response_model=List[ToolOut], tags=["Dashboard – Tools"])
def list_tools(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return db.query(ToolCatalog).order_by(ToolCatalog.name).all()


# ── POLICY CRUD ───────────────────────────────────

@app.get("/api/v1/policy", response_model=List[PolicyOut], tags=["Dashboard – Policy"])
def get_policies(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    org_id = user["org_id"]
    rows = (
        db.query(Policy, ToolCatalog)
        .join(ToolCatalog, Policy.tool_id == ToolCatalog.id)
        .filter(Policy.org_id == org_id)
        .all()
    )
    result = []
    for pol, tool in rows:
        alt_name = None
        if pol.alternative_tool_id:
            alt = db.query(ToolCatalog).get(pol.alternative_tool_id)
            alt_name = alt.name if alt else None
        result.append(PolicyOut(
            id=pol.id, tool_id=pol.tool_id, tool_name=tool.name,
            tool_domain=tool.domain, action=pol.action,
            alternative_tool_id=pol.alternative_tool_id,
            alternative_name=alt_name,
        ))
    return result


from fastapi import Request

@app.put("/api/v1/policy", tags=["Dashboard – Policy"])
def upsert_policy(body: PolicyItem, request: Request, db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    org_id = user["org_id"]
    existing = db.query(Policy).filter(Policy.org_id == org_id, Policy.tool_id == body.tool_id).first()
    
    before_state = None
    if existing:
        before_state = {"action": existing.action, "alternative_tool_id": existing.alternative_tool_id}
        existing.action = body.action
        existing.alternative_tool_id = body.alternative_tool_id
        action_type = "UPDATE_POLICY"
    else:
        db.add(Policy(org_id=org_id, tool_id=body.tool_id, action=body.action, alternative_tool_id=body.alternative_tool_id))
        action_type = "CREATE_POLICY"

    after_state = {"action": body.action, "alternative_tool_id": body.alternative_tool_id}

    admin = db.query(Admin).filter(Admin.email == user["sub"]).first()
    tool = db.query(ToolCatalog).get(body.tool_id)
    
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    db.add(AuditLog(
        org_id=org_id, admin_id=admin.id,
        action=action_type,
        rule_before=json.dumps(before_state) if before_state else None,
        rule_after=json.dumps(after_state),
        reason=None,
        ip_address=ip_address,
        user_agent=user_agent
    ))
    db.commit()
    return {"status": "saved"}


@app.delete("/api/v1/policy/{policy_id}", tags=["Dashboard – Policy"])
def delete_policy(policy_id: int, request: Request, db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    pol = db.query(Policy).get(policy_id)
    if not pol or pol.org_id != user["org_id"]:
        raise HTTPException(404, "Policy not found")
        
    before_state = {"action": pol.action, "alternative_tool_id": pol.alternative_tool_id}
    
    admin = db.query(Admin).filter(Admin.email == user["sub"]).first()
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    db.add(AuditLog(
        org_id=user["org_id"], admin_id=admin.id,
        action="DELETE_POLICY",
        rule_before=json.dumps(before_state),
        rule_after=None,
        reason=None,
        ip_address=ip_address,
        user_agent=user_agent
    ))
        
    db.delete(pol)
    db.commit()
    return {"status": "deleted"}


# ── ANALYTICS ─────────────────────────────────────

from fastapi.responses import StreamingResponse
import csv
import io

@app.get("/api/v1/analytics/summary", tags=["Dashboard – Analytics"])
def analytics_summary(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    org_id = user["org_id"]
    since = datetime.utcnow() - timedelta(days=30)
    total = db.query(func.count(UsageEvent.id)).filter(
        UsageEvent.org_id == org_id, UsageEvent.timestamp >= since
    ).scalar() or 0
    warned = db.query(func.count(UsageEvent.id)).filter(
        UsageEvent.org_id == org_id, UsageEvent.timestamp >= since, UsageEvent.policy_action == "warn"
    ).scalar() or 0
    blocked = db.query(func.count(UsageEvent.id)).filter(
        UsageEvent.org_id == org_id, UsageEvent.timestamp >= since, UsageEvent.policy_action == "block"
    ).scalar() or 0
    unique_users = db.query(func.count(func.distinct(UsageEvent.user_hash))).filter(
        UsageEvent.org_id == org_id, UsageEvent.timestamp >= since
    ).scalar() or 0
    return {"total": total, "warned": warned, "blocked": blocked, "unique_users": unique_users}

@app.get("/api/v1/analytics/export", tags=["Dashboard – Analytics"])
def export_csv(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    org_id = user["org_id"]
    events = db.query(UsageEvent).filter(UsageEvent.org_id == org_id).order_by(UsageEvent.timestamp.desc()).limit(1000).all()

    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "Event ID", "Timestamp", "User Hash", "Device Hash", "Domain", 
        "Tool Name", "Category", "Policy Action", "Rule ID", "Browser", "Ext Version"
    ])
    
    for e in events:
        writer.writerow([
            e.id, 
            e.timestamp.isoformat(), 
            e.user_hash, 
            e.device_hash, 
            e.domain, 
            e.tool_name, 
            e.category, 
            e.policy_action, 
            e.policy_rule_id, 
            e.browser, 
            e.extension_version
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=shadow_ai_export_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"}
    )
    
@app.get("/api/v1/alerts", response_model=List[AlertOut], tags=["Dashboard – Audit"])
def fetch_alerts(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    org_id = user["org_id"]
    alerts = (
        db.query(AlertEvent)
        .filter(AlertEvent.org_id == org_id)
        .order_by(AlertEvent.timestamp.desc())
        .limit(limit)
        .all()
    )
    return alerts


@app.get("/api/v1/analytics/top-tools", response_model=List[TopToolItem], tags=["Dashboard – Analytics"])
def top_tools(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    org_id = user["org_id"]
    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(UsageEvent.domain, func.count(UsageEvent.id).label("cnt"))
        .filter(UsageEvent.org_id == org_id, UsageEvent.timestamp >= since)
        .group_by(UsageEvent.domain)
        .order_by(func.count(UsageEvent.id).desc())
        .limit(10)
        .all()
    )
    result = []
    for domain, cnt in rows:
        tool = db.query(ToolCatalog).filter(ToolCatalog.domain == domain).first()
        result.append(TopToolItem(
            name=tool.name if tool else domain, domain=domain,
            category=tool.category if tool else "unknown", count=cnt,
        ))
    return result


@app.get("/api/v1/analytics/trends", response_model=List[TrendPoint], tags=["Dashboard – Analytics"])
def trends(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    org_id = user["org_id"]
    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(func.date(UsageEvent.timestamp).label("day"), func.count(UsageEvent.id).label("cnt"))
        .filter(UsageEvent.org_id == org_id, UsageEvent.timestamp >= since)
        .group_by(func.date(UsageEvent.timestamp))
        .order_by(func.date(UsageEvent.timestamp))
        .all()
    )
    return [TrendPoint(date=str(d), count=c) for d, c in rows]


@app.get("/api/v1/analytics/risk", response_model=List[RiskScoreOut], tags=["Dashboard – Analytics"])
def risk_scores(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    org_id = user["org_id"]
    since = datetime.utcnow() - timedelta(days=30)
    rows = (
        db.query(ToolCatalog.category, func.count(UsageEvent.id), func.avg(ToolCatalog.base_risk_score))
        .join(ToolCatalog, UsageEvent.domain == ToolCatalog.domain)
        .filter(UsageEvent.org_id == org_id, UsageEvent.timestamp >= since)
        .group_by(ToolCatalog.category)
        .all()
    )
    return [RiskScoreOut(category=cat, event_count=cnt, score=round(float(avg), 1)) for cat, cnt, avg in rows]


# ── AUDIT LOGS ────────────────────────────────────

@app.get("/api/v1/audit-logs", response_model=List[AuditLogOut], tags=["Dashboard – Audit"])
def audit_logs(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    org_id = user["org_id"]
    rows = (
        db.query(AuditLog, Admin.email)
        .join(Admin, AuditLog.admin_id == Admin.id)
        .filter(AuditLog.org_id == org_id)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        AuditLogOut(id=log.id, admin_email=email, action=log.action, rule_before=log.rule_before, rule_after=log.rule_after, reason=log.reason, timestamp=log.timestamp, ip_address=log.ip_address, user_agent=log.user_agent)
        for log, email in rows
    ]


# ══════════════════════════════════════════════════════════════════
#                          MODULE B
#         Breach Monitor + Recovery Kit (Personal Endpoints)
# ══════════════════════════════════════════════════════════════════


# ── AUTH (Personal) ───────────────────────────────

@app.post("/api/v1/personal/auth/register", response_model=PersonalTokenResponse, tags=["Auth – Personal"])
def personal_register(body: PersonalRegisterRequest, db: Session = Depends(get_db)):
    if db.query(PersonalUser).filter(PersonalUser.email == body.email).first():
        raise HTTPException(400, "Email already registered")
    user = PersonalUser(
        email=body.email,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({
        "sub": user.email,
        "personal_user_id": user.id,
        "tier": user.tier,
    })
    return PersonalTokenResponse(
        access_token=token, user_id=user.id,
        tier=user.tier, max_emails=user.max_emails,
    )


@app.post("/api/v1/personal/auth/login", response_model=PersonalTokenResponse, tags=["Auth – Personal"])
def personal_login(body: PersonalLoginRequest, db: Session = Depends(get_db)):
    user = db.query(PersonalUser).filter(PersonalUser.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    user.last_login = datetime.utcnow()
    db.commit()
    token = create_access_token({
        "sub": user.email,
        "personal_user_id": user.id,
        "tier": user.tier,
    })
    return PersonalTokenResponse(
        access_token=token, user_id=user.id,
        tier=user.tier, max_emails=user.max_emails,
    )


# ── BREACH MONITORING ────────────────────────────

@app.post("/api/v1/breach/monitor-email", status_code=201, tags=["Breach Monitor"])
def add_monitored_email(
    body: MonitorEmailRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    pu = _get_personal_user(user, db)

    email_h = hash_email(body.email)
    existing = db.query(MonitoredEmail).filter(
        MonitoredEmail.user_id == pu.id,
        MonitoredEmail.email_hash == email_h,
    ).first()
    if existing:
        raise HTTPException(400, "Email already being monitored")

    # Check tier limits
    current_count = db.query(func.count(MonitoredEmail.id)).filter(
        MonitoredEmail.user_id == pu.id, MonitoredEmail.is_active == True
    ).scalar() or 0
    if current_count >= pu.max_emails:
        raise HTTPException(
            403,
            f"Email limit reached ({pu.max_emails}). Upgrade to monitor more emails.",
        )

    me = MonitoredEmail(
        user_id=pu.id,
        email_encrypted=encrypt_email(body.email),
        email_hash=email_h,
        label=body.label,
    )
    db.add(me)
    db.commit()
    db.refresh(me)

    return {
        "id": me.id,
        "email_masked": mask_email(body.email),
        "label": me.label,
        "status": "active",
        "added_at": me.added_at.isoformat(),
    }


@app.get("/api/v1/breach/monitored-emails", tags=["Breach Monitor"])
def list_monitored_emails(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    pu = _get_personal_user(user, db)
    emails = db.query(MonitoredEmail).filter(
        MonitoredEmail.user_id == pu.id,
    ).order_by(MonitoredEmail.added_at.desc()).all()

    result = []
    for me in emails:
        breach_count = db.query(func.count(BreachEvent.id)).filter(
            BreachEvent.monitored_email_id == me.id
        ).scalar() or 0
        try:
            raw_email = decrypt_email(me.email_encrypted)
            masked = mask_email(raw_email)
        except Exception:
            masked = "***@***"
        result.append({
            "id": me.id,
            "email_masked": masked,
            "label": me.label,
            "is_active": me.is_active,
            "added_at": me.added_at.isoformat(),
            "last_checked": me.last_checked.isoformat() if me.last_checked else None,
            "breach_count": breach_count,
        })

    return {
        "emails": result,
        "tier": pu.tier,
        "max_emails": pu.max_emails,
        "used": len([e for e in emails if e.is_active]),
    }


@app.delete("/api/v1/breach/monitored-email/{email_id}", tags=["Breach Monitor"])
def remove_monitored_email(
    email_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    pu = _get_personal_user(user, db)
    me = db.query(MonitoredEmail).filter(
        MonitoredEmail.id == email_id,
        MonitoredEmail.user_id == pu.id,
    ).first()
    if not me:
        raise HTTPException(404, "Monitored email not found")
    db.delete(me)
    db.commit()
    return {"status": "deleted"}


@app.get("/api/v1/breach/status", tags=["Breach Monitor"])
def breach_status(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    pu = _get_personal_user(user, db)
    emails = db.query(MonitoredEmail).filter(MonitoredEmail.user_id == pu.id).all()

    total_breaches = 0
    email_results = []

    for me in emails:
        breaches = db.query(BreachEvent).filter(
            BreachEvent.monitored_email_id == me.id
        ).order_by(BreachEvent.discovered_at.desc()).all()

        try:
            masked = mask_email(decrypt_email(me.email_encrypted))
        except Exception:
            masked = "***@***"

        breach_list = []
        for b in breaches:
            data_classes = json.loads(b.data_classes) if b.data_classes else []
            breach_list.append({
                "id": b.id,
                "source_name": b.source_name,
                "breach_date": str(b.breach_date) if b.breach_date else None,
                "data_classes": data_classes,
                "severity": b.severity,
                "discovered_at": b.discovered_at.isoformat(),
            })

        total_breaches += len(breaches)
        email_results.append({
            "id": me.id,
            "email_masked": masked,
            "label": me.label,
            "last_checked": me.last_checked.isoformat() if me.last_checked else None,
            "breach_count": len(breaches),
            "breaches": breach_list,
        })

    # Count unresolved = breaches without a completed recovery plan
    resolved_breach_ids = set()
    plans = db.query(RecoveryPlan).filter(
        RecoveryPlan.user_id == pu.id,
        RecoveryPlan.status == "completed",
    ).all()
    for p in plans:
        if p.breach_event_id:
            resolved_breach_ids.add(p.breach_event_id)
    unresolved = total_breaches - len(resolved_breach_ids)

    return {
        "monitored_emails": email_results,
        "total_breaches": total_breaches,
        "unresolved": max(0, unresolved),
    }


@app.post("/api/v1/breach/run-check", tags=["Breach Monitor"])
async def run_breach_check(
    body: RunCheckRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    pu = _get_personal_user(user, db)
    me = db.query(MonitoredEmail).filter(
        MonitoredEmail.id == body.monitored_email_id,
        MonitoredEmail.user_id == pu.id,
    ).first()
    if not me:
        raise HTTPException(404, "Monitored email not found")

    # Decrypt email for breach check
    try:
        raw_email = decrypt_email(me.email_encrypted)
    except Exception:
        raise HTTPException(500, "Failed to decrypt email")

    # Run breach check
    checker = get_breach_checker()
    results = await checker.check(raw_email)

    # Store new breaches (deduplicate by source_name)
    new_count = 0
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
            # Create alert
            db.add(BreachAlert(
                user_id=pu.id,
                breach_event_id=be.id,
                channel="email",
            ))
            # Send notification
            send_breach_email(
                to_email=raw_email,
                breach_source=breach.source_name,
                breach_date=str(breach.breach_date) if breach.breach_date else None,
                data_classes=breach.data_classes,
            )
            new_count += 1

    me.last_checked = datetime.utcnow()
    db.commit()

    return {
        "status": "completed",
        "message": f"Found {len(results)} breach(es). {new_count} new.",
        "new_breaches": new_count,
    }


# ── RECOVERY KIT ─────────────────────────────────

@app.get("/api/v1/recovery/platforms", tags=["Recovery Kit"])
def list_platforms():
    """List all supported platforms with recovery templates."""
    return {"platforms": get_supported_platforms()}


@app.post("/api/v1/recovery/plan", status_code=201, tags=["Recovery Kit"])
def create_recovery_plan(
    body: CreateRecoveryPlanRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    pu = _get_personal_user(user, db)

    # Get template
    template = get_recovery_template(body.platform)
    if not template:
        raise HTTPException(400, f"Unsupported platform: {body.platform}. Supported: {get_supported_platforms()}")

    # Check for existing plan for this platform
    existing = db.query(RecoveryPlan).filter(
        RecoveryPlan.user_id == pu.id,
        RecoveryPlan.platform == body.platform.lower(),
        RecoveryPlan.status != "completed",
    ).first()
    if existing:
        raise HTTPException(400, "An active recovery plan already exists for this platform")

    plan = RecoveryPlan(
        user_id=pu.id,
        breach_event_id=body.breach_event_id,
        platform=body.platform.lower(),
    )
    db.add(plan)
    db.flush()

    for task_tmpl in template:
        db.add(RecoveryTask(
            plan_id=plan.id,
            task_key=task_tmpl["task_key"],
            title=task_tmpl["title"],
            description=task_tmpl.get("description"),
            help_url=task_tmpl.get("help_url"),
            sort_order=task_tmpl.get("sort_order", 0),
        ))

    db.commit()
    db.refresh(plan)

    return _plan_to_dict(plan)


@app.get("/api/v1/recovery/plans", tags=["Recovery Kit"])
def list_recovery_plans(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    pu = _get_personal_user(user, db)
    plans = db.query(RecoveryPlan).filter(
        RecoveryPlan.user_id == pu.id,
    ).order_by(RecoveryPlan.created_at.desc()).all()

    return {"plans": [_plan_to_dict(p) for p in plans]}


@app.get("/api/v1/recovery/plan/{plan_id}", tags=["Recovery Kit"])
def get_recovery_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    pu = _get_personal_user(user, db)
    plan = db.query(RecoveryPlan).filter(
        RecoveryPlan.id == plan_id,
        RecoveryPlan.user_id == pu.id,
    ).first()
    if not plan:
        raise HTTPException(404, "Recovery plan not found")

    return _plan_to_dict(plan)


@app.patch("/api/v1/recovery/task/{task_id}", tags=["Recovery Kit"])
def update_recovery_task(
    task_id: int,
    body: UpdateTaskRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    pu = _get_personal_user(user, db)
    task = db.query(RecoveryTask).join(RecoveryPlan).filter(
        RecoveryTask.id == task_id,
        RecoveryPlan.user_id == pu.id,
    ).first()
    if not task:
        raise HTTPException(404, "Task not found")

    task.is_completed = body.is_completed
    task.completed_at = datetime.utcnow() if body.is_completed else None

    # Update plan status
    plan = task.plan
    all_tasks = db.query(RecoveryTask).filter(RecoveryTask.plan_id == plan.id).all()
    completed = sum(1 for t in all_tasks if t.is_completed or (t.id == task_id and body.is_completed))
    total = len(all_tasks)

    if completed == total:
        plan.status = "completed"
        plan.completed_at = datetime.utcnow()
    elif completed > 0:
        plan.status = "in_progress"
        plan.completed_at = None
    else:
        plan.status = "pending"
        plan.completed_at = None

    db.commit()
    db.refresh(task)

    return {
        "id": task.id,
        "is_completed": task.is_completed,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "plan_status": plan.status,
        "plan_progress": completed / total if total else 0,
    }


def _plan_to_dict(plan: RecoveryPlan) -> dict:
    """Convert RecoveryPlan ORM object to response dict."""
    tasks = [
        {
            "id": t.id,
            "task_key": t.task_key,
            "title": t.title,
            "description": t.description,
            "help_url": t.help_url,
            "is_completed": t.is_completed,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            "sort_order": t.sort_order,
        }
        for t in plan.tasks
    ]
    completed = sum(1 for t in plan.tasks if t.is_completed)
    total = len(plan.tasks)

    return {
        "id": plan.id,
        "platform": plan.platform,
        "status": plan.status,
        "created_at": plan.created_at.isoformat(),
        "completed_at": plan.completed_at.isoformat() if plan.completed_at else None,
        "tasks": tasks,
        "progress": completed / total if total else 0,
    }


# ── SECURITY SCORE ────────────────────────────────

@app.get("/api/v1/security-score", tags=["Security Score"])
def get_security_score(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    pu = _get_personal_user(user, db)
    score_data = _calculate_security_score(pu, db)

    # Save snapshot
    ss = SecurityScore(
        user_id=pu.id,
        score=score_data["score"],
        grade=score_data["grade"],
        breakdown=json.dumps(score_data["breakdown"]),
    )
    db.add(ss)
    db.commit()

    return score_data


@app.get("/api/v1/security-score/history", tags=["Security Score"])
def score_history(
    limit: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    pu = _get_personal_user(user, db)
    scores = db.query(SecurityScore).filter(
        SecurityScore.user_id == pu.id,
    ).order_by(SecurityScore.calculated_at.desc()).limit(limit).all()

    return {
        "history": [
            {
                "score": s.score,
                "grade": s.grade,
                "calculated_at": s.calculated_at.isoformat(),
            }
            for s in reversed(scores)
        ]
    }


def _calculate_security_score(user: PersonalUser, db: Session) -> dict:
    """Calculate security score (0-100) with grade and recommendations."""
    # Count totals
    total_breaches = 0
    for me in user.monitored_emails:
        total_breaches += db.query(func.count(BreachEvent.id)).filter(
            BreachEvent.monitored_email_id == me.id
        ).scalar() or 0

    plans = db.query(RecoveryPlan).filter(RecoveryPlan.user_id == user.id).all()
    completed_plans = [p for p in plans if p.status == "completed"]

    all_tasks = db.query(RecoveryTask).join(RecoveryPlan).filter(
        RecoveryPlan.user_id == user.id
    ).all()
    total_tasks = len(all_tasks)
    completed_tasks = sum(1 for t in all_tasks if t.is_completed)

    # Score calculation
    score = 100

    # Deduct for unresolved breaches (-15 each, max -45)
    unresolved = total_breaches - len(completed_plans)
    breach_penalty = min(45, max(0, unresolved) * 15)
    score -= breach_penalty

    # Deduct for incomplete tasks (-3 each, max -30)
    incomplete_tasks = total_tasks - completed_tasks
    task_penalty = min(30, incomplete_tasks * 3)
    score -= task_penalty

    # Bonus for having recovery plans (+5 each, max +15)
    plan_bonus = min(15, len(plans) * 5)
    score = min(100, score + plan_bonus)

    # Bonus for monitoring emails (+5, max +10)
    email_bonus = min(10, len(user.monitored_emails) * 5)
    score = min(100, score + email_bonus)

    score = max(0, score)

    # Grade
    if score >= 90:
        grade = "A"
    elif score >= 80:
        grade = "B"
    elif score >= 70:
        grade = "C"
    elif score >= 60:
        grade = "D"
    else:
        grade = "F"

    # Recommendations
    recommendations = []
    if unresolved > 0:
        recommendations.append(f"Create recovery plans for {unresolved} unresolved breach(es)")
    if incomplete_tasks > 0:
        recommendations.append(f"Complete {incomplete_tasks} remaining recovery task(s)")
    if len(user.monitored_emails) == 0:
        recommendations.append("Add at least one email to monitor for breaches")
    if total_breaches == 0 and len(user.monitored_emails) > 0:
        recommendations.append("Run a breach check on your monitored emails")
    if not recommendations:
        recommendations.append("Great job! Keep monitoring your accounts regularly.")

    return {
        "score": score,
        "grade": grade,
        "breakdown": {
            "total_breaches": total_breaches,
            "breaches_with_recovery": len(completed_plans),
            "tasks_completed": completed_tasks,
            "tasks_total": total_tasks,
            "emails_monitored": len(user.monitored_emails),
            "last_calculated": datetime.utcnow().isoformat(),
        },
        "recommendations": recommendations,
    }


# ══════════════════════════════════════════════════
#  HEALTH
# ══════════════════════════════════════════════════

@app.get("/health")
def health():
    return {"status": "ok", "modules": ["shadow_ai", "breach_monitor"]}
