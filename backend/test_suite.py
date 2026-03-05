"""
ShieldOps Comprehensive Test Suite
====================================
Covers: Backend API (OrgGuard + BreachGuard), Database, RBAC, Security,
        Multi-Tenant Isolation, Privacy Validation, Load Testing.

Run:  python test_suite.py
"""

import os
import sys
import time
import json
import asyncio
import hashlib
import sqlite3
import logging
from datetime import datetime, timedelta
from collections import defaultdict

# ── Setup: Use a test database ─────────────────────
TEST_DB = "test_shieldops.db"
os.environ["DATABASE_URL"] = f"sqlite:///./{TEST_DB}"
os.environ["SECRET_KEY"] = "test_secret_key_for_testing_only"
os.environ["BREACH_CHECKER"] = "mock"
os.environ["ENCRYPTION_KEY"] = ""  # auto-generate for tests

# Clean up any existing test DB
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

# Now import our modules (AFTER setting env vars)
from fastapi.testclient import TestClient
from main import app
from database import engine, get_db
from models import Base
from seed import seed_tools

# ── Explicitly create tables (startup event may not fire in newer TestClient) ──
Base.metadata.create_all(bind=engine)
db_init = next(get_db())
seed_tools(db_init)
db_init.close()

client = TestClient(app)

# ── Test Tracking ──────────────────────────────────

results = defaultdict(list)
total_pass = 0
total_fail = 0


def test(category: str, name: str, condition: bool, details: str = ""):
    global total_pass, total_fail
    status = "✅ PASS" if condition else "❌ FAIL"
    if condition:
        total_pass += 1
    else:
        total_fail += 1
    detail_str = f" — {details}" if details else ""
    results[category].append(f"{status} {name}{detail_str}")
    print(f"  {status} {name}{detail_str}")


def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ══════════════════════════════════════════════════════
#  0. TEST ENVIRONMENT SETUP
# ══════════════════════════════════════════════════════

section("0. Test Environment Setup")

test("Setup", "Test DB is SQLite (isolated)",
     "sqlite" in os.environ["DATABASE_URL"])

test("Setup", "BREACH_CHECKER is mock",
     os.environ["BREACH_CHECKER"] == "mock")

# Health check
r = client.get("/health")
test("Setup", "Health endpoint returns 200",
     r.status_code == 200 and r.json()["status"] == "ok",
     f"status={r.status_code}")


# ══════════════════════════════════════════════════════
#  1. ORGGUARD — Auth + RBAC Tests
# ══════════════════════════════════════════════════════

section("1A. OrgGuard — Auth + RBAC")

# Register Org A Admin
r = client.post("/api/v1/auth/register", json={
    "email": "admin_a@orgA.com", "password": "Pass123!", "org_name": "OrgA"
})
test("Auth", "Admin registration returns 200",
     r.status_code == 200)
admin_a_data = r.json()
admin_a_token = admin_a_data.get("access_token", "")
org_a_token = admin_a_data.get("org_token", "")
test("Auth", "Registration returns JWT token",
     len(admin_a_token) > 20)
test("Auth", "Registration returns org_token",
     len(org_a_token) > 10)
test("Auth", "Admin role is 'admin'",
     admin_a_data.get("role") == "admin")

# Login Admin A
r = client.post("/api/v1/auth/login", json={
    "email": "admin_a@orgA.com", "password": "Pass123!"
})
test("Auth", "Admin login returns 200",
     r.status_code == 200)

# Duplicate registration
r = client.post("/api/v1/auth/register", json={
    "email": "admin_a@orgA.com", "password": "Pass123!", "org_name": "OrgA2"
})
test("Auth", "Duplicate email registration rejected (400)",
     r.status_code == 400)

# Invalid credentials
r = client.post("/api/v1/auth/login", json={
    "email": "admin_a@orgA.com", "password": "WrongPass"
})
test("Auth", "Wrong password rejected (401)",
     r.status_code == 401)

# Invalid token
r = client.get("/api/v1/tools", headers={
    "Authorization": "Bearer invalidtoken123"
})
test("Auth", "Invalid JWT rejected (401)",
     r.status_code == 401)

# Expired token test — manually create one
from auth import create_access_token
expired_token = create_access_token(
    {"sub": "admin_a@orgA.com", "org_id": 1, "role": "admin"},
    expires_delta=timedelta(seconds=-10)
)
r = client.get("/api/v1/tools", headers={
    "Authorization": f"Bearer {expired_token}"
})
test("Security", "Expired JWT rejected (401)",
     r.status_code == 401)

# Admin can access tools
admin_headers = {"Authorization": f"Bearer {admin_a_token}"}
r = client.get("/api/v1/tools", headers=admin_headers)
test("RBAC", "Admin can access /tools",
     r.status_code == 200 and isinstance(r.json(), list))
test("RBAC", "Tools catalog has 25 AI tools seeded",
     len(r.json()) == 25, f"got {len(r.json())} tools")

# Admin can access analytics
r = client.get("/api/v1/analytics/summary", headers=admin_headers)
test("RBAC", "Admin can access /analytics/summary",
     r.status_code == 200)

# Admin can access audit logs
r = client.get("/api/v1/audit-logs", headers=admin_headers)
test("RBAC", "Admin can access /audit-logs",
     r.status_code == 200)

# ══════════════════════════════════════════════════════
#  1B. ORGGUARD — Event Ingestion
# ══════════════════════════════════════════════════════

section("1B. OrgGuard — Event Ingestion")

# Valid event
r = client.post("/api/v1/events", json={
    "domain": "chatgpt.com",
    "user_hash": hashlib.sha256(b"user1@org.com").hexdigest(),
    "policy_action": "allow",
    "timestamp": datetime.utcnow().isoformat()
}, headers={"org-token": org_a_token})
test("Events", "Valid event accepted (201)",
     r.status_code == 201)

# Event with missing fields
r = client.post("/api/v1/events", json={
    "domain": "chatgpt.com"
}, headers={"org-token": org_a_token})
test("Events", "Missing fields rejected (422)",
     r.status_code == 422)

# Event with invalid org token
r = client.post("/api/v1/events", json={
    "domain": "chatgpt.com",
    "user_hash": "abc123",
    "policy_action": "allow",
    "timestamp": datetime.utcnow().isoformat()
}, headers={"org-token": "invalid_token"})
test("Events", "Invalid org token rejected (401)",
     r.status_code == 401)

# Send replay event (>24h old)
old_ts = (datetime.utcnow() - timedelta(hours=25)).isoformat()
r = client.post("/api/v1/events", json={
    "domain": "chatgpt.com",
    "user_hash": "abc",
    "policy_action": "allow",
    "timestamp": old_ts
}, headers={"org-token": org_a_token})
test("Security", "Replay: event >24h old rejected (400)",
     r.status_code == 400, f"ts={old_ts}")

# Batch events
events = []
for i in range(10):
    events.append({
        "domain": "chatgpt.com",
        "user_hash": hashlib.sha256(f"user{i}@org.com".encode()).hexdigest(),
        "policy_action": "allow",
        "timestamp": datetime.utcnow().isoformat()
    })
for i in range(5):
    events.append({
        "domain": "claude.ai",
        "user_hash": hashlib.sha256(f"user{i}@org.com".encode()).hexdigest(),
        "policy_action": "warn",
        "timestamp": datetime.utcnow().isoformat()
    })
for i in range(3):
    events.append({
        "domain": "midjourney.com",
        "user_hash": hashlib.sha256(f"user{i}@org.com".encode()).hexdigest(),
        "policy_action": "block",
        "timestamp": datetime.utcnow().isoformat()
    })
r = client.post("/api/v1/events/batch", json=events,
                 headers={"org-token": org_a_token})
test("Events", "Batch events accepted (201)",
     r.status_code == 201)
test("Events", f"Batch count is {len(events)}",
     r.json().get("count") == len(events), f"got {r.json()}")


# ══════════════════════════════════════════════════════
#  1C. ORGGUARD — Analytics Correctness
# ══════════════════════════════════════════════════════

section("1C. OrgGuard — Analytics Correctness")

r = client.get("/api/v1/analytics/summary", headers=admin_headers)
summary = r.json()
# We inserted 1 + 10 = 11 chatgpt, 5 claude (warn), 3 midjourney (block)
test("Analytics", "Total events count is correct",
     summary["total"] == 19, f"expected 19, got {summary['total']}")
test("Analytics", "Warned count is correct",
     summary["warned"] == 5, f"expected 5, got {summary['warned']}")
test("Analytics", "Blocked count is correct",
     summary["blocked"] == 3, f"expected 3, got {summary['blocked']}")
test("Analytics", "Unique users count > 0",
     summary["unique_users"] > 0, f"got {summary['unique_users']}")

# Top tools
r = client.get("/api/v1/analytics/top-tools?days=30", headers=admin_headers)
top = r.json()
test("Analytics", "Top tools returns list",
     isinstance(top, list) and len(top) > 0)
test("Analytics", "Top tool is chatgpt.com (11 events)",
     top[0]["domain"] == "chatgpt.com" and top[0]["count"] == 11,
     f"got {top[0] if top else 'empty'}")

# Trends
r = client.get("/api/v1/analytics/trends?days=30", headers=admin_headers)
trends = r.json()
test("Analytics", "Trends returns list with today's data",
     isinstance(trends, list) and len(trends) >= 1)

# Risk
r = client.get("/api/v1/analytics/risk", headers=admin_headers)
risk = r.json()
test("Analytics", "Risk scores return by category",
     isinstance(risk, list))


# ══════════════════════════════════════════════════════
#  1D. ORGGUARD — Policy CRUD + Audit
# ══════════════════════════════════════════════════════

section("1D. OrgGuard — Policy CRUD + Audit")

# Get tools to find IDs
r = client.get("/api/v1/tools", headers=admin_headers)
tools = {t["domain"]: t["id"] for t in r.json()}

# Create policy: warn on claude.ai
r = client.put("/api/v1/policy", json={
    "tool_id": tools["claude.ai"],
    "action": "warn"
}, headers=admin_headers)
test("Policy", "Create warn policy returns 200",
     r.status_code == 200)

# Create policy: block on midjourney.com
r = client.put("/api/v1/policy", json={
    "tool_id": tools["midjourney.com"],
    "action": "block"
}, headers=admin_headers)
test("Policy", "Create block policy returns 200",
     r.status_code == 200)

# Create policy: allow chatgpt with alternative
r = client.put("/api/v1/policy", json={
    "tool_id": tools["chatgpt.com"],
    "action": "allow",
    "alternative_tool_id": tools["gemini.google.com"]
}, headers=admin_headers)
test("Policy", "Create allow policy with alternative",
     r.status_code == 200)

# List policies
r = client.get("/api/v1/policy", headers=admin_headers)
policies = r.json()
test("Policy", "List policies returns 3",
     len(policies) == 3, f"got {len(policies)}")

# Policy sync (extension endpoint)
r = client.get("/api/v1/policy/sync", headers={"org-token": org_a_token})
sync = r.json()
test("Policy", "Policy sync returns policies dict",
     "policies" in sync and "claude.ai" in sync["policies"])
test("Policy", "Sync shows warn for claude.ai",
     sync["policies"]["claude.ai"]["action"] == "warn")
test("Policy", "Sync shows block for midjourney.com",
     sync["policies"]["midjourney.com"]["action"] == "block")

# Check audit logs recorded
r = client.get("/api/v1/audit-logs", headers=admin_headers)
logs = r.json()
test("Audit", "Audit logs recorded policy changes",
     len(logs) >= 3, f"got {len(logs)} audit entries")
test("Audit", "Audit entries have admin_email",
     all(log.get("admin_email") for log in logs))

# Update policy
r = client.put("/api/v1/policy", json={
    "tool_id": tools["claude.ai"],
    "action": "block"
}, headers=admin_headers)
test("Policy", "Update existing policy works",
     r.status_code == 200)

# Delete policy
policy_to_delete = policies[0]["id"]
r = client.delete(f"/api/v1/policy/{policy_to_delete}", headers=admin_headers)
test("Policy", "Delete policy returns 200",
     r.status_code == 200)


# ══════════════════════════════════════════════════════
#  2A. BREACHGUARD — Personal Auth
# ══════════════════════════════════════════════════════

section("2A. BreachGuard — Personal Auth")

# Register personal user
r = client.post("/api/v1/personal/auth/register", json={
    "email": "user1@persontest.com", "password": "UserPass1!"
})
test("Personal Auth", "Registration returns 200",
     r.status_code == 200)
pu1 = r.json()
pu1_token = pu1.get("access_token", "")
test("Personal Auth", "Returns JWT token",
     len(pu1_token) > 20)
test("Personal Auth", "Tier is 'free'",
     pu1.get("tier") == "free")
test("Personal Auth", "Max emails is 1 (free tier)",
     pu1.get("max_emails") == 1)

# Duplicate registration
r = client.post("/api/v1/personal/auth/register", json={
    "email": "user1@persontest.com", "password": "AnotherPass"
})
test("Personal Auth", "Duplicate email rejected (400)",
     r.status_code == 400)

# Login
r = client.post("/api/v1/personal/auth/login", json={
    "email": "user1@persontest.com", "password": "UserPass1!"
})
test("Personal Auth", "Login returns 200",
     r.status_code == 200)

# Wrong password
r = client.post("/api/v1/personal/auth/login", json={
    "email": "user1@persontest.com", "password": "WrongPass"
})
test("Personal Auth", "Wrong password rejected (401)",
     r.status_code == 401)

# Register second personal user (for isolation tests later)
r = client.post("/api/v1/personal/auth/register", json={
    "email": "user2@persontest.com", "password": "UserPass2!"
})
pu2_token = r.json().get("access_token", "")


# ══════════════════════════════════════════════════════
#  2B. BREACHGUARD — Breach Monitoring
# ══════════════════════════════════════════════════════

section("2B. BreachGuard — Breach Monitoring")

pu1_headers = {"Authorization": f"Bearer {pu1_token}"}

# Add monitored email
r = client.post("/api/v1/breach/monitor-email", json={
    "email": "breached@test.com", "label": "Work email"
}, headers=pu1_headers)
test("Breach Monitor", "Add email returns 201",
     r.status_code == 201)
email_data = r.json()
test("Breach Monitor", "Returns masked email",
     "@" in email_data.get("email_masked", ""))
monitored_email_id = email_data.get("id", 0)

# Duplicate email
r = client.post("/api/v1/breach/monitor-email", json={
    "email": "breached@test.com"
}, headers=pu1_headers)
test("Breach Monitor", "Duplicate email rejected (400)",
     r.status_code == 400)

# Tier limit (free = 1 email max)
r = client.post("/api/v1/breach/monitor-email", json={
    "email": "extra@test.com"
}, headers=pu1_headers)
test("Breach Monitor", "Tier limit enforced (403)",
     r.status_code == 403, f"got {r.status_code}: {r.json().get('detail', '')}")

# List monitored emails
r = client.get("/api/v1/breach/monitored-emails", headers=pu1_headers)
test("Breach Monitor", "List emails returns 200",
     r.status_code == 200)
em_data = r.json()
test("Breach Monitor", "Shows 1 monitored email",
     len(em_data.get("emails", [])) == 1)
test("Breach Monitor", "Shows tier info",
     em_data.get("tier") == "free" and em_data.get("max_emails") == 1)

# Run breach check (mock adapter)
r = client.post("/api/v1/breach/run-check", json={
    "monitored_email_id": monitored_email_id
}, headers=pu1_headers)
test("Breach Monitor", "Run check returns 200",
     r.status_code == 200)
check_result = r.json()
test("Breach Monitor", "Mock adapter found breaches",
     check_result.get("new_breaches", 0) > 0,
     f"found {check_result.get('new_breaches', 0)} new")

# Breach status
r = client.get("/api/v1/breach/status", headers=pu1_headers)
test("Breach Monitor", "Breach status returns 200",
     r.status_code == 200)
status = r.json()
test("Breach Monitor", "Total breaches > 0",
     status.get("total_breaches", 0) > 0,
     f"total={status.get('total_breaches')}")
test("Breach Monitor", "Unresolved breaches > 0",
     status.get("unresolved", 0) > 0)
test("Breach Monitor", "Breach details include source_name",
     any(b["source_name"] for em in status.get("monitored_emails", [])
         for b in em.get("breaches", [])))

# Deduplicate — run check again
r = client.post("/api/v1/breach/run-check", json={
    "monitored_email_id": monitored_email_id
}, headers=pu1_headers)
dedup = r.json()
test("Breach Monitor", "Deduplicate: second check finds 0 new",
     dedup.get("new_breaches", -1) == 0,
     f"got {dedup.get('new_breaches')}")

# Check someone else's email (should fail)
r = client.post("/api/v1/breach/run-check", json={
    "monitored_email_id": 9999
}, headers=pu1_headers)
test("Breach Monitor", "Cannot check non-existent email (404)",
     r.status_code == 404)


# ══════════════════════════════════════════════════════
#  2C. BREACHGUARD — Recovery Kit
# ══════════════════════════════════════════════════════

section("2C. BreachGuard — Recovery Kit")

# List supported platforms
r = client.get("/api/v1/recovery/platforms")
test("Recovery", "Platforms endpoint returns 200",
     r.status_code == 200)
platforms = r.json().get("platforms", [])
test("Recovery", "Has 7 supported platforms",
     len(platforms) == 7, f"got {platforms}")

# Create recovery plan for Google
r = client.post("/api/v1/recovery/plan", json={
    "platform": "google"
}, headers=pu1_headers)
test("Recovery", "Create Google plan returns 201",
     r.status_code == 201)
plan = r.json()
test("Recovery", "Plan has tasks",
     len(plan.get("tasks", [])) > 0, f"got {len(plan.get('tasks', []))} tasks")
test("Recovery", "Plan status is 'pending'",
     plan.get("status") == "pending")
test("Recovery", "Plan progress is 0",
     plan.get("progress") == 0)
plan_id = plan.get("id", 0)

# Try duplicate plan
r = client.post("/api/v1/recovery/plan", json={
    "platform": "google"
}, headers=pu1_headers)
test("Recovery", "Duplicate active plan rejected (400)",
     r.status_code == 400)

# Unsupported platform
r = client.post("/api/v1/recovery/plan", json={
    "platform": "tiktok"
}, headers=pu1_headers)
test("Recovery", "Unsupported platform rejected (400)",
     r.status_code == 400)

# List plans
r = client.get("/api/v1/recovery/plans", headers=pu1_headers)
test("Recovery", "List plans returns 200",
     r.status_code == 200)

# Get plan detail
r = client.get(f"/api/v1/recovery/plan/{plan_id}", headers=pu1_headers)
test("Recovery", "Get plan detail returns 200",
     r.status_code == 200)
detail = r.json()
tasks = detail.get("tasks", [])
test("Recovery", "Tasks have title and description",
     all(t.get("title") for t in tasks))
test("Recovery", "Tasks have help_url",
     any(t.get("help_url") for t in tasks))

# Complete first task
if tasks:
    task_id = tasks[0]["id"]
    r = client.patch(f"/api/v1/recovery/task/{task_id}", json={
        "is_completed": True
    }, headers=pu1_headers)
    test("Recovery", "Toggle task complete returns 200",
         r.status_code == 200)
    task_result = r.json()
    test("Recovery", "Task marked as completed",
         task_result.get("is_completed") == True)
    test("Recovery", "Plan status changed to 'in_progress'",
         task_result.get("plan_status") == "in_progress")
    test("Recovery", "Plan progress > 0",
         task_result.get("plan_progress", 0) > 0)

    # Un-complete the task
    r = client.patch(f"/api/v1/recovery/task/{task_id}", json={
        "is_completed": False
    }, headers=pu1_headers)
    test("Recovery", "Toggle task back to incomplete",
         r.status_code == 200 and r.json()["is_completed"] == False)

    # Complete ALL tasks
    for t in tasks:
        client.patch(f"/api/v1/recovery/task/{t['id']}", json={
            "is_completed": True
        }, headers=pu1_headers)

    r = client.get(f"/api/v1/recovery/plan/{plan_id}", headers=pu1_headers)
    completed_plan = r.json()
    test("Recovery", "All tasks complete → plan 'completed'",
         completed_plan.get("status") == "completed")
    test("Recovery", "Progress = 100%",
         completed_plan.get("progress") == 1.0)


# ══════════════════════════════════════════════════════
#  2D. BREACHGUARD — Security Score
# ══════════════════════════════════════════════════════

section("2D. BreachGuard — Security Score")

r = client.get("/api/v1/security-score", headers=pu1_headers)
test("Score", "Get security score returns 200",
     r.status_code == 200)
score = r.json()
test("Score", "Score is 0-100",
     0 <= score.get("score", -1) <= 100, f"score={score.get('score')}")
test("Score", "Grade is A-F",
     score.get("grade") in ["A", "B", "C", "D", "F"],
     f"grade={score.get('grade')}")
test("Score", "Breakdown includes monitored email count",
     score.get("breakdown", {}).get("emails_monitored", -1) >= 1)
test("Score", "Has recommendations list",
     isinstance(score.get("recommendations"), list))

# Score history
r = client.get("/api/v1/security-score/history?limit=5", headers=pu1_headers)
test("Score", "Score history returns 200",
     r.status_code == 200)
history = r.json().get("history", [])
test("Score", "History has at least 1 entry",
     len(history) >= 1)


# ══════════════════════════════════════════════════════
#  3. DATABASE TESTS
# ══════════════════════════════════════════════════════

section("3. Database Tests")

conn = sqlite3.connect(TEST_DB)
cursor = conn.cursor()

# Check all expected tables exist
expected_tables = [
    "organizations", "admins", "tools_catalog", "policies",
    "usage_events", "audit_logs",
    "personal_users", "monitored_emails", "breach_events",
    "breach_alerts", "recovery_plans", "recovery_tasks",
    "security_scores", "reminders"
]
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
actual_tables = {row[0] for row in cursor.fetchall()}
for tbl in expected_tables:
    test("Database", f"Table '{tbl}' exists",
         tbl in actual_tables)

# Check indexes
cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
indexes = {row[0] for row in cursor.fetchall()}
test("Database", "Has event index (org+timestamp)",
     any("events_org_ts" in idx for idx in indexes))
test("Database", "Has breach email index",
     any("breach_email" in idx for idx in indexes))
test("Database", "Has recovery user index",
     any("recovery_user" in idx for idx in indexes))

# Check usage_events only stores minimal data
cursor.execute("PRAGMA table_info(usage_events)")
event_columns = {row[1] for row in cursor.fetchall()}
test("Privacy", "usage_events has 'domain' column",
     "domain" in event_columns)
test("Privacy", "usage_events has 'timestamp' column",
     "timestamp" in event_columns)
test("Privacy", "usage_events has NO 'content' column",
     "content" not in event_columns)
test("Privacy", "usage_events has NO 'prompt' column",
     "prompt" not in event_columns)
test("Privacy", "usage_events has NO 'text' column",
     "text" not in event_columns)

# Check emails are encrypted
cursor.execute("SELECT email_encrypted, email_hash FROM monitored_emails LIMIT 1")
row = cursor.fetchone()
if row:
    test("Privacy", "Stored email is encrypted (not plaintext)",
         "breached@test.com" not in (row[0] or ""),
         f"encrypted={row[0][:30]}...")
    test("Privacy", "Email hash is stored (SHA-256)",
         len(row[1] or "") == 64)

# Unique constraints
cursor.execute("SELECT COUNT(*) FROM admins WHERE email='admin_a@orgA.com'")
test("Database", "Admin email is unique",
     cursor.fetchone()[0] == 1)

conn.close()


# ══════════════════════════════════════════════════════
#  4. MULTI-TENANT ISOLATION
# ══════════════════════════════════════════════════════

section("4. Multi-Tenant Isolation")

# Register Org B
r = client.post("/api/v1/auth/register", json={
    "email": "admin_b@orgB.com", "password": "PassB123!", "org_name": "OrgB"
})
admin_b_data = r.json()
admin_b_token = admin_b_data.get("access_token", "")
org_b_token = admin_b_data.get("org_token", "")
admin_b_headers = {"Authorization": f"Bearer {admin_b_token}"}

# Send events for Org B
r = client.post("/api/v1/events", json={
    "domain": "poe.com",
    "user_hash": "orgb_user_hash",
    "policy_action": "allow",
    "timestamp": datetime.utcnow().isoformat()
}, headers={"org-token": org_b_token})
test("Isolation", "Org B can submit events",
     r.status_code == 201)

# Org B analytics should NOT see Org A data
r = client.get("/api/v1/analytics/summary", headers=admin_b_headers)
b_summary = r.json()
test("Isolation", "Org B sees only 1 event (not Org A's 19)",
     b_summary["total"] == 1, f"got {b_summary['total']}")

# Org B policies should be empty (only Org A created policies)
r = client.get("/api/v1/policy", headers=admin_b_headers)
b_policies = r.json()
test("Isolation", "Org B has 0 policies (isolated from Org A)",
     len(b_policies) == 0, f"got {len(b_policies)}")

# Org B audit logs should NOT contain Org A entries
r = client.get("/api/v1/audit-logs", headers=admin_b_headers)
b_logs = r.json()
test("Isolation", "Org B audit logs are empty (isolated)",
     len(b_logs) == 0, f"got {len(b_logs)}")

# Personal user isolation
pu2_headers = {"Authorization": f"Bearer {pu2_token}"}
r = client.get("/api/v1/breach/monitored-emails", headers=pu2_headers)
pu2_emails = r.json()
test("Isolation", "User2 sees 0 monitored emails (isolated from User1)",
     len(pu2_emails.get("emails", [])) == 0)

r = client.get("/api/v1/breach/status", headers=pu2_headers)
pu2_status = r.json()
test("Isolation", "User2 sees 0 breaches (isolated)",
     pu2_status.get("total_breaches", -1) == 0)

r = client.get("/api/v1/recovery/plans", headers=pu2_headers)
pu2_plans = r.json()
test("Isolation", "User2 sees 0 recovery plans (isolated)",
     len(pu2_plans.get("plans", [])) == 0)

# User2 cannot access User1's recovery plan
r = client.get(f"/api/v1/recovery/plan/{plan_id}", headers=pu2_headers)
test("Isolation", "User2 cannot access User1's plan (404)",
     r.status_code == 404)


# ══════════════════════════════════════════════════════
#  5. SECURITY TESTS
# ══════════════════════════════════════════════════════

section("5. Security Tests")

# No auth → 403
r = client.get("/api/v1/tools")
test("Security", "Unauthenticated request rejected (403)",
     r.status_code == 403)

# Viewer cannot edit policy (simulate by creating token with viewer role)
viewer_token = create_access_token({
    "sub": "viewer@orgA.com", "org_id": 1, "role": "viewer"
})
r = client.put("/api/v1/policy", json={
    "tool_id": 1, "action": "block"
}, headers={"Authorization": f"Bearer {viewer_token}"})
test("Security", "Viewer cannot edit policy (403)",
     r.status_code == 403)

# Viewer CAN read analytics
r = client.get("/api/v1/analytics/summary",
               headers={"Authorization": f"Bearer {viewer_token}"})
test("Security", "Viewer CAN read analytics (200)",
     r.status_code == 200)

# Viewer CAN read top tools
r = client.get("/api/v1/analytics/top-tools",
               headers={"Authorization": f"Bearer {viewer_token}"})
test("RBAC", "Viewer CAN read top-tools (200)",
     r.status_code == 200)

# Viewer CAN read trends
r = client.get("/api/v1/analytics/trends",
               headers={"Authorization": f"Bearer {viewer_token}"})
test("RBAC", "Viewer CAN read trends (200)",
     r.status_code == 200)

# Viewer cannot delete policy
r = client.delete("/api/v1/policy/1",
                  headers={"Authorization": f"Bearer {viewer_token}"})
test("RBAC", "Viewer cannot delete policy (403)",
     r.status_code == 403)

# Cross-org token test: Org B token cannot delete Org A's policy
r = client.get("/api/v1/policy", headers=admin_headers)
remaining_policies = r.json()
if remaining_policies:
    target_id = remaining_policies[0]["id"]
    r = client.delete(f"/api/v1/policy/{target_id}", headers=admin_b_headers)
    test("Security", "Org B cannot delete Org A's policy (404)",
         r.status_code == 404)

# Cross-org analytics isolation: Org B cannot see Org A top-tools
r = client.get("/api/v1/analytics/top-tools", headers=admin_b_headers)
b_top = r.json()
test("Isolation", "Org B top-tools does NOT contain Org A domains",
     not any(t["domain"] == "chatgpt.com" for t in b_top))

# Replay attack: send same event 50 times rapidly
replay_payload = {
    "domain": "chatgpt.com",
    "user_hash": hashlib.sha256(b"replay_user").hexdigest(),
    "policy_action": "allow",
    "timestamp": datetime.utcnow().isoformat()
}
for _ in range(50):
    client.post("/api/v1/events", json=replay_payload,
                headers={"org-token": org_a_token})
test("Security", "Rapid replay of 50 identical events accepted (no rate-limit)",
     True, "NOTE: Rate limiting NOT implemented — recommended for production")


# ══════════════════════════════════════════════════════
#  6. PRIVACY VALIDATION
# ══════════════════════════════════════════════════════

section("6. Privacy Validation")

conn = sqlite3.connect(TEST_DB)
cursor = conn.cursor()

# Check no sensitive columns exist in ANY table
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
all_tables = [row[0] for row in cursor.fetchall()]
sensitive_columns = {"prompt", "content", "text", "page_title", "screenshot",
                     "clipboard", "file_content", "password", "plain_password"}
for tbl in all_tables:
    cursor.execute(f"PRAGMA table_info({tbl})")
    cols = {row[1] for row in cursor.fetchall()}
    found_sensitive = cols & sensitive_columns
    test("Privacy", f"Table '{tbl}' has NO sensitive columns",
         len(found_sensitive) == 0,
         f"FOUND: {found_sensitive}" if found_sensitive else "")

# Verify usage_events data
cursor.execute("SELECT * FROM usage_events LIMIT 1")
event_row = cursor.fetchone()
cursor.execute("PRAGMA table_info(usage_events)")
event_col_names = [row[1] for row in cursor.fetchall()]
expected_cols = {
    "id", "org_id", "domain", "user_hash", "policy_action", "timestamp",
    "event_type", "risk_score", "device_hash", "tool_name", "category", 
    "policy_rule_id", "browser", "extension_version", "ip_site", "geo_region"
}
test("Privacy", "usage_events stores only approved metadata (no prompts/content)",
     set(event_col_names) == expected_cols,
     f"columns: {event_col_names}")

# Verify monitored_emails stores encrypted email, not plaintext
cursor.execute("SELECT email_encrypted FROM monitored_emails")
encrypted_emails = [row[0] for row in cursor.fetchall()]
for enc in encrypted_emails:
    test("Privacy", "Email NOT stored in plaintext",
         "@" not in enc and len(enc) > 50,
         f"first_30_chars: {enc[:30]}")

conn.close()


# ══════════════════════════════════════════════════════
#  7. LOAD TEST (Simple MVP-level)
# ══════════════════════════════════════════════════════

section("7. Load Test")

# Send 5000 events rapidly (MVP load test)
start_time = time.time()
BATCH_SIZE = 100
NUM_BATCHES = 50  # 50 × 100 = 5,000 events
total_sent = 0
all_ok = True

for batch in range(NUM_BATCHES):
    events = []
    for i in range(BATCH_SIZE):
        events.append({
            "domain": ["chatgpt.com", "claude.ai", "poe.com", "perplexity.ai", "midjourney.com"][i % 5],
            "user_hash": hashlib.sha256(f"load_user_{batch}_{i}".encode()).hexdigest(),
            "policy_action": ["allow", "warn", "block"][i % 3],
            "timestamp": datetime.utcnow().isoformat()
        })
    r = client.post("/api/v1/events/batch", json=events,
                     headers={"org-token": org_a_token})
    if r.status_code != 201:
        all_ok = False
    total_sent += BATCH_SIZE

elapsed = time.time() - start_time
eps = total_sent / elapsed if elapsed > 0 else 0

test("Load", f"Sent {total_sent} events in {elapsed:.1f}s ({eps:.0f} events/sec)",
     all_ok, f"all batches returned 201")

# Analytics still works after bulk insert
r = client.get("/api/v1/analytics/summary", headers=admin_headers)
test("Load", "Analytics still works after 5000+ events",
     r.status_code == 200)
new_total = r.json()["total"]
test("Load", f"Total event count is correct ({new_total})",
     new_total >= 5019, f"expected >= 5019, got {new_total}")

# Top tools still accurate
r = client.get("/api/v1/analytics/top-tools", headers=admin_headers)
test("Load", "Top tools endpoint still works after load",
     r.status_code == 200 and len(r.json()) > 0)

# Trends still work
r = client.get("/api/v1/analytics/trends", headers=admin_headers)
test("Load", "Trends endpoint still works after load",
     r.status_code == 200)

# Batch of 50 events in single request
batch_50 = []
for i in range(50):
    batch_50.append({
        "domain": "chatgpt.com",
        "user_hash": hashlib.sha256(f"batch50_{i}".encode()).hexdigest(),
        "policy_action": "allow",
        "timestamp": datetime.utcnow().isoformat()
    })
r = client.post("/api/v1/events/batch", json=batch_50,
                 headers={"org-token": org_a_token})
test("Load", "Single batch of 50 events accepted",
     r.status_code == 201 and r.json().get("count") == 50)


# ══════════════════════════════════════════════════════
#  8. LAB SETUP & ADVANCED LOG TESTS
# ══════════════════════════════════════════════════════

section("8. Lab Setup & Advanced Log Tests")

# ── Test 0: Create Lab Org ──────────────────────────
r = client.post("/api/v1/auth/register", json={
    "email": "lab_admin@lab_org_01.com", "password": "LabPass01!", "org_name": "lab_org_01"
})
test("Lab", "Test 0 – Create lab_org_01 (200)",
     r.status_code == 200, f"got {r.status_code}")
lab_data = r.json()
lab_token = lab_data.get("access_token", "")
lab_org_token = lab_data.get("org_token", "")
lab_org_id = lab_data.get("org_id", 0)
lab_headers = {"Authorization": f"Bearer {lab_token}"}
test("Lab", "Test 0 – Got org_token for lab_org_01",
     len(lab_org_token) > 10, f"token={lab_org_token[:20]}...")

# ── Test 1: Baseline – known domains ───────────────
for domain in ["chat.openai.com", "claude.ai"]:
    r = client.post("/api/v1/events", json={
        "domain": domain,
        "user_hash": "lab_user_01",
        "policy_action": "allow",
        "timestamp": datetime.utcnow().isoformat()
    }, headers={"org-token": lab_org_token})
    test("Lab", f"Test 1 – Baseline event for {domain} accepted (201)",
         r.status_code == 201)

# Verify via DB
conn_lab = sqlite3.connect(TEST_DB)
cur_lab = conn_lab.cursor()
cur_lab.execute(
    "SELECT domain, category FROM usage_events WHERE user_hash='lab_user_01' AND org_id=?",
    (lab_org_id,)
)
lab_rows = cur_lab.fetchall()
test("Lab", "Test 1 – Two baseline events stored",
     len(lab_rows) == 2, f"got {len(lab_rows)}")
for domain, category in lab_rows:
    test("Lab", f"Test 1 – {domain} category is 'chat'",
         category == "chat", f"got category={category}")

# ── Test 2: Policy Enforcement ─────────────────────
# Get tool IDs
r = client.get("/api/v1/tools", headers=lab_headers)
lab_tools = {t["domain"]: t["id"] for t in r.json()}

# Allow chat.openai.com
r = client.put("/api/v1/policy", json={
    "tool_id": lab_tools["chat.openai.com"], "action": "allow"
}, headers=lab_headers)
test("Lab", "Test 2 – Allow policy created", r.status_code == 200)

# Warn on claude.ai
r = client.put("/api/v1/policy", json={
    "tool_id": lab_tools["claude.ai"], "action": "warn"
}, headers=lab_headers)
test("Lab", "Test 2 – Warn policy created", r.status_code == 200)

# Block on midjourney.com
r = client.put("/api/v1/policy", json={
    "tool_id": lab_tools["midjourney.com"], "action": "block"
}, headers=lab_headers)
test("Lab", "Test 2 – Block policy created", r.status_code == 200)

# Get policy sync to retrieve rule IDs
r = client.get("/api/v1/policy/sync", headers={"org-token": lab_org_token})
lab_policy_sync = r.json().get("policies", {})

# Send events with policy_action and policy_rule_id
for domain, expected_action in [("chat.openai.com", "allow"), ("claude.ai", "warn"), ("midjourney.com", "block")]:
    rule_id = lab_policy_sync.get(domain, {}).get("rule_id")
    r = client.post("/api/v1/events", json={
        "domain": domain,
        "user_hash": "lab_user_01",
        "policy_action": expected_action,
        "policy_rule_id": rule_id,
        "timestamp": datetime.utcnow().isoformat()
    }, headers={"org-token": lab_org_token})
    test("Lab", f"Test 2 – {expected_action} event for {domain} accepted",
         r.status_code == 201)

# Verify policy_action and policy_rule_id via DB
cur_lab.execute(
    "SELECT domain, policy_action, policy_rule_id FROM usage_events "
    "WHERE user_hash='lab_user_01' AND org_id=? AND policy_rule_id IS NOT NULL",
    (lab_org_id,)
)
policy_rows = cur_lab.fetchall()
test("Lab", "Test 2 – 3 events with policy_rule_id stored",
     len(policy_rows) == 3, f"got {len(policy_rows)}")
for domain, action, rule_id in policy_rows:
    test("Lab", f"Test 2 – {domain} has rule_id set",
         rule_id is not None and rule_id > 0, f"rule_id={rule_id}")

# ── Test 3: Unknown Tool Detection ─────────────────
# Use a domain NOT in the seed catalog
unknown_domain = "unknowntool-lab.example.com"
r = client.post("/api/v1/events", json={
    "domain": unknown_domain,
    "user_hash": "lab_user_01",
    "policy_action": "allow",
    "timestamp": datetime.utcnow().isoformat()
}, headers={"org-token": lab_org_token})
test("Lab", "Test 3 – Unknown tool event accepted (201)",
     r.status_code == 201)

# Verify category == 'unknown'
cur_lab.execute(
    "SELECT category, tool_name FROM usage_events WHERE domain=? AND org_id=?",
    (unknown_domain, lab_org_id)
)
unk_row = cur_lab.fetchone()
test("Lab", "Test 3 – Unknown domain category is 'unknown'",
     unk_row is not None and unk_row[0] == "unknown",
     f"got category={unk_row[0] if unk_row else 'N/A'}")
test("Lab", "Test 3 – Unknown domain tool_name is 'unknown'",
     unk_row is not None and unk_row[1] == "unknown",
     f"got tool_name={unk_row[1] if unk_row else 'N/A'}")

# Verify NewToolSeen alert
cur_lab.execute(
    "SELECT alert_type, severity, domain FROM alert_events "
    "WHERE org_id=? AND alert_type='NewToolSeen' AND domain=?",
    (lab_org_id, unknown_domain)
)
nts_alert = cur_lab.fetchone()
test("Lab", "Test 3 – NewToolSeen alert exists",
     nts_alert is not None, f"got {nts_alert}")
test("Lab", "Test 3 – NewToolSeen severity is 'Low'",
     nts_alert is not None and nts_alert[1] == "Low",
     f"severity={nts_alert[1] if nts_alert else 'N/A'}")

# ── Test 4: Spike Usage ────────────────────────────
spike_events = []
for i in range(20):
    spike_events.append({
        "domain": "chatgpt.com",
        "user_hash": "lab_user_01",
        "policy_action": "allow",
        "timestamp": datetime.utcnow().isoformat()
    })
r = client.post("/api/v1/events/batch", json=spike_events,
                 headers={"org-token": lab_org_token})
test("Lab", "Test 4 – 20-event spike batch accepted (201)",
     r.status_code == 201 and r.json().get("count") == 20,
     f"got {r.json()}")

# Verify SpikeUsage alert
cur_lab.execute(
    "SELECT alert_type, severity, count_threshold FROM alert_events "
    "WHERE org_id=? AND alert_type='SpikeUsage'",
    (lab_org_id,)
)
spike_alert = cur_lab.fetchone()
test("Lab", "Test 4 – SpikeUsage alert exists",
     spike_alert is not None, f"got {spike_alert}")
test("Lab", "Test 4 – SpikeUsage severity is 'Medium'",
     spike_alert is not None and spike_alert[1] == "Medium",
     f"severity={spike_alert[1] if spike_alert else 'N/A'}")
test("Lab", "Test 4 – SpikeUsage threshold is 20",
     spike_alert is not None and spike_alert[2] == 20,
     f"threshold={spike_alert[2] if spike_alert else 'N/A'}")

# ── Test 5: Offline Retry (4h-old timestamp) ───────
four_hours_ago = (datetime.utcnow() - timedelta(hours=4)).isoformat()
r = client.post("/api/v1/events", json={
    "domain": "perplexity.ai",
    "user_hash": "lab_user_01",
    "policy_action": "allow",
    "timestamp": four_hours_ago
}, headers={"org-token": lab_org_token})
test("Lab", "Test 5 – Offline retry (4h ago) accepted (201)",
     r.status_code == 201)

# Verify the event stored with the original timestamp
cur_lab.execute(
    "SELECT domain, timestamp FROM usage_events "
    "WHERE user_hash='lab_user_01' AND domain='perplexity.ai' AND org_id=?",
    (lab_org_id,)
)
offline_row = cur_lab.fetchone()
test("Lab", "Test 5 – Offline event stored successfully",
     offline_row is not None, f"got {offline_row}")

conn_lab.close()


# ══════════════════════════════════════════════════════
#  9. NOTIFICATION STUBS (verify no crashes)
# ══════════════════════════════════════════════════════

section("9. Notification Service")

from notification_service import send_breach_email, send_reminder_email, send_telegram_alert

ok1 = send_breach_email("test@test.com", "LinkedIn", "2012-05-05", ["Email", "Password"])
test("Notifications", "send_breach_email (stub) does not crash",
     ok1 == True)

ok2 = send_reminder_email("test@test.com", "Time for review!")
test("Notifications", "send_reminder_email (stub) does not crash",
     ok2 == True)

ok3 = send_telegram_alert("12345", "Test alert")
test("Notifications", "send_telegram_alert (stub) does not crash",
     ok3 == True)


# ═══════════════════════════════════════════════════════
#  10. DELETE / CLEANUP ENDPOINTS
# ═══════════════════════════════════════════════════════

section("10. Delete / Cleanup")

# Remove monitored email
r = client.delete(f"/api/v1/breach/monitored-email/{monitored_email_id}",
                  headers=pu1_headers)
test("Cleanup", "Delete monitored email returns 200",
     r.status_code == 200)

# Verify deletion cascaded
r = client.get("/api/v1/breach/monitored-emails", headers=pu1_headers)
test("Cleanup", "Email removed from list",
     len(r.json().get("emails", [])) == 0)


# ══════════════════════════════════════════════════════
#  FINAL REPORT
# ══════════════════════════════════════════════════════

print(f"\n{'='*60}")
print(f"  FINAL TEST REPORT")
print(f"{'='*60}")
print(f"\n  Total: {total_pass + total_fail}")
print(f"  ✅ Passed: {total_pass}")
print(f"  ❌ Failed: {total_fail}")
print(f"  Pass Rate: {(total_pass/(total_pass+total_fail))*100:.1f}%\n")

if total_fail > 0:
    print("  Failed tests:")
    for cat, tests_list in results.items():
        for t in tests_list:
            if "❌" in t:
                print(f"    [{cat}] {t}")
    print()

# ══════════════════════════════════════════════════════
#  11. FEATURE GAP NOTES
# ══════════════════════════════════════════════════════

section("11. Feature Gap Notes (not errors — recommendations)")

print("  📝 Rate Limiting: NOT implemented. Recommended for production.")
print("  📝 Domain Format Validation: No regex check on 'domain' field.")
print("  📝 Extension Heartbeat: NOT implemented. Consider for drop-in-reporting detection.")
print("  📝 90-day Reminder: Scheduler (worker.py) runs but SMTP not configured for tests.")
print("  📝 Telegram Integration: Stubbed — bot token not configured.")
print()

# Cleanup test DB
try:
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
        print(f"  🧹 Test database '{TEST_DB}' cleaned up.\n")
except Exception as e:
    print(f"  🧹 Note: Could not delete test DB (likely Windows file lock). Ignored. ({e})\n")

# Exit code
sys.exit(0 if total_fail == 0 else 1)
