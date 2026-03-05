"""
Shadow AI Detector – FastAPI Backend
=====================================
Privacy-first: Only domain, timestamp, org_id, user_hash are ever stored.
"""

import secrets
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, cast, Date
from sqlalchemy.orm import Session

from database import engine, get_db
from models import Base, Organization, Admin, ToolCatalog, Policy, UsageEvent, AuditLog
from schemas import (
    LoginRequest, RegisterRequest, TokenResponse,
    EventCreate, EventOut,
    PolicyItem, PolicyOut, PolicySyncOut,
    ToolOut, TopToolItem, TrendPoint, RiskScoreOut,
    AuditLogOut,
)
from auth import (
    hash_password, verify_password,
    create_access_token, get_current_user, require_admin,
)
from seed import seed_tools

# ── App setup ─────────────────────────────────────
app = FastAPI(title="Shadow AI Detector API", version="1.0.0")

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
#  AUTH
# ══════════════════════════════════════════════════

@app.post("/api/v1/auth/register", response_model=TokenResponse)
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


@app.post("/api/v1/auth/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.email == body.email).first()
    if not admin or not verify_password(body.password, admin.password_hash):
        raise HTTPException(401, "Invalid credentials")
    org = db.query(Organization).get(admin.org_id)
    token = create_access_token({"sub": admin.email, "org_id": org.id, "role": admin.role})
    return TokenResponse(access_token=token, role=admin.role, org_id=org.id, org_token=org.token)


# ══════════════════════════════════════════════════
#  EXTENSION ENDPOINTS  (auth via org-token header)
# ══════════════════════════════════════════════════

def _get_org_by_token(org_token: str, db: Session) -> Organization:
    org = db.query(Organization).filter(Organization.token == org_token).first()
    if not org:
        raise HTTPException(401, "Invalid org token")
    return org


@app.post("/api/v1/events", status_code=201)
def record_event(event: EventCreate, db: Session = Depends(get_db), org_token: str = Header(None)):
    org = _get_org_by_token(org_token, db)
    # Reject events > 24 h old (replay protection)
    if abs((datetime.utcnow() - event.timestamp).total_seconds()) > 86400:
        raise HTTPException(400, "Timestamp out of range")
    row = UsageEvent(
        org_id=org.id,
        domain=event.domain,
        user_hash=event.user_hash,
        action_taken=event.action_taken,
        timestamp=event.timestamp,
    )
    db.add(row)
    db.commit()
    return {"status": "recorded"}


@app.post("/api/v1/events/batch", status_code=201)
def record_events_batch(events: List[EventCreate], db: Session = Depends(get_db), org_token: str = Header(None)):
    org = _get_org_by_token(org_token, db)
    now = datetime.utcnow()
    rows = []
    for e in events:
        if abs((now - e.timestamp).total_seconds()) > 86400:
            continue  # silently skip stale events
        rows.append(UsageEvent(
            org_id=org.id, domain=e.domain,
            user_hash=e.user_hash, action_taken=e.action_taken,
            timestamp=e.timestamp,
        ))
    db.add_all(rows)
    db.commit()
    return {"status": "recorded", "count": len(rows)}


@app.get("/api/v1/policy/sync", response_model=PolicySyncOut)
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
        out[tool.domain] = {"action": pol.action, "alternative": alt_name}
    return PolicySyncOut(policies=out)


# ══════════════════════════════════════════════════
#  DASHBOARD – TOOLS CATALOG
# ══════════════════════════════════════════════════

@app.get("/api/v1/tools", response_model=List[ToolOut])
def list_tools(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return db.query(ToolCatalog).order_by(ToolCatalog.name).all()


# ══════════════════════════════════════════════════
#  DASHBOARD – POLICY CRUD
# ══════════════════════════════════════════════════

@app.get("/api/v1/policy", response_model=List[PolicyOut])
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


@app.put("/api/v1/policy")
def upsert_policy(body: PolicyItem, db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    org_id = user["org_id"]
    existing = db.query(Policy).filter(Policy.org_id == org_id, Policy.tool_id == body.tool_id).first()
    if existing:
        existing.action = body.action
        existing.alternative_tool_id = body.alternative_tool_id
    else:
        db.add(Policy(org_id=org_id, tool_id=body.tool_id, action=body.action, alternative_tool_id=body.alternative_tool_id))
    # Audit log
    admin = db.query(Admin).filter(Admin.email == user["sub"]).first()
    tool = db.query(ToolCatalog).get(body.tool_id)
    db.add(AuditLog(
        org_id=org_id, admin_id=admin.id,
        action="policy_update",
        detail=f"Set {tool.name} → {body.action}",
    ))
    db.commit()
    return {"status": "saved"}


@app.delete("/api/v1/policy/{policy_id}")
def delete_policy(policy_id: int, db: Session = Depends(get_db), user: dict = Depends(require_admin)):
    pol = db.query(Policy).get(policy_id)
    if not pol or pol.org_id != user["org_id"]:
        raise HTTPException(404, "Policy not found")
    db.delete(pol)
    db.commit()
    return {"status": "deleted"}


# ══════════════════════════════════════════════════
#  DASHBOARD – ANALYTICS
# ══════════════════════════════════════════════════

@app.get("/api/v1/analytics/summary")
def analytics_summary(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    org_id = user["org_id"]
    since = datetime.utcnow() - timedelta(days=30)
    total = db.query(func.count(UsageEvent.id)).filter(
        UsageEvent.org_id == org_id, UsageEvent.timestamp >= since
    ).scalar() or 0
    warned = db.query(func.count(UsageEvent.id)).filter(
        UsageEvent.org_id == org_id, UsageEvent.timestamp >= since, UsageEvent.action_taken == "warn"
    ).scalar() or 0
    blocked = db.query(func.count(UsageEvent.id)).filter(
        UsageEvent.org_id == org_id, UsageEvent.timestamp >= since, UsageEvent.action_taken == "block"
    ).scalar() or 0
    unique_users = db.query(func.count(func.distinct(UsageEvent.user_hash))).filter(
        UsageEvent.org_id == org_id, UsageEvent.timestamp >= since
    ).scalar() or 0
    return {"total": total, "warned": warned, "blocked": blocked, "unique_users": unique_users}


@app.get("/api/v1/analytics/top-tools", response_model=List[TopToolItem])
def top_tools(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    org_id = user["org_id"]
    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(
            UsageEvent.domain,
            func.count(UsageEvent.id).label("cnt"),
        )
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
            name=tool.name if tool else domain,
            domain=domain,
            category=tool.category if tool else "unknown",
            count=cnt,
        ))
    return result


@app.get("/api/v1/analytics/trends", response_model=List[TrendPoint])
def trends(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    org_id = user["org_id"]
    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(
            cast(UsageEvent.timestamp, Date).label("day"),
            func.count(UsageEvent.id).label("cnt"),
        )
        .filter(UsageEvent.org_id == org_id, UsageEvent.timestamp >= since)
        .group_by("day")
        .order_by("day")
        .all()
    )
    return [TrendPoint(date=str(d), count=c) for d, c in rows]


@app.get("/api/v1/analytics/risk", response_model=List[RiskScoreOut])
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


# ══════════════════════════════════════════════════
#  DASHBOARD – AUDIT LOGS
# ══════════════════════════════════════════════════

@app.get("/api/v1/audit-logs", response_model=List[AuditLogOut])
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
        AuditLogOut(id=log.id, admin_email=email, action=log.action, detail=log.detail, timestamp=log.timestamp)
        for log, email in rows
    ]


# ══════════════════════════════════════════════════
#  HEALTH
# ══════════════════════════════════════════════════

@app.get("/health")
def health():
    return {"status": "ok"}
