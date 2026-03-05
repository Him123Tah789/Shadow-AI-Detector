# Lightweight Shadow AI Detector (Org)

## 1) PRODUCT OVERVIEW

**The Problem (Shadow AI):**
Employees are increasingly using unapproved, unsanctioned AI tools (like random summarizers, unregulated chatbots, code generators) to do their work. This "Shadow AI" creates massive risks for organizations: sensitive company data, source code, or PII might be pasted into tools that train on user input or have poor security. Companies lack visibility into what AI tools are being used, leaving them blind to data leaks and compliance violations.

**Target Users & Value Proposition:**
- **Primary Users:** IT Admins, CISO, Security & Compliance Teams.
- **Value Proposition:** Gain instant visibility into organizational AI usage and enforce basic governance (Warn/Block) *without* deploying heavy, invasive spyware. It respects employee privacy while protecting company data.

**What it IS / What it is NOT (Privacy Boundaries):**
- ✅ **IS:** A domain-level traffic analyzer targeting known AI URLs.
- ✅ **IS:** A lightweight enforcer for allow/warn/block policies.
- ✅ **IS:** A high-level analytics dashboard for organizational risk.
- ❌ **IS NOT:** A keylogger or screen recorder.
- ❌ **IS NOT:** A prompt-capture tool (we NEVER see what the user types or uploads).
- ❌ **IS NOT:** A general web-filter (only looks at AI-categorized domains).

---

## 2) SYSTEM ARCHITECTURE

**Modules:**
1. **Browser Extension:** Lightweight domain sensor and policy enforcer (Chrome/Edge).
2. **API Backend:** Python/FastAPI service for receiving telemetry and serving policies.
3. **Database:** PostgreSQL for storing events, policies, and the AI tool catalog.
4. **Policy Engine:** Logic evaluating domain vs. org policy (cached at edge/extension).
5. **Admin Dashboard:** Next.js web portal for IT admins to view analytics and set rules.
6. **Tool Catalog:** Maintained list of AI domains categorized by risk (Chat, Code, Image, File).

**Architecture Diagram:**
```text
[ Browser Extension ] <--- (Cache Policy) --- [ FastAPI Backend ]
       |                                            |
  (Captures Domain)                                 |
       |                                            |
       v                                            v
(Allow/Warn/Block UI)                          [ PostgreSQL ]
       |                                      (Policies, Events,
  (POST /events) -----> [ FastAPI Backend ]    Tool Catalog)
                                                    ^
                                                    |
[ IT Admin ] <------- [ Next.js Dashboard ] --------+
```

**Data Flow:**
- **Admin Policy Update:** Admin logs into dashboard -> PUT `/policy` -> Backend -> DB.
- **Detect / Allow / Warn / Block:** 
  1. Extension detects navigation to `chatgpt.com`.
  2. Extension checks local cache of Org Policy.
  3. If **Allow**: Extension logs domain (silently) -> POST `/events`.
  4. If **Warn**: Extension injects a banner/notification ("This tool is unapproved. Recommended: Copilot"). Logs event.
  5. If **Block**: Extension redirects tab to local block page (`blocked.html`). Logs event.

**Privacy & Security Design:**
- **Data Minimization:** We only send `{ timestamp, domain, org_id, user_hash }`.
- **User Hashing:** We do not send emails or names. The extension generates a static UUID or hashes the employee email locally (e.g., `SHA-256(email + org_salt)`) to track unique users without exposing identity.
- **Retention:** Events are automatically aggregated/rolled-up after 30 days and raw logs are purged.

---

## 3) MVP FEATURE LIST

**Must-Have Features:**
- **Extension:** Detect URL visits, compare against cached catalog/policy logic, enforce Warn/Block, batch and send logs to backend.
- **Backend:** Receive & store usage POST events, serve policy config, provide basic REST API for analytics.
- **Dashboard:** Auth login, simple dashboard with Top Tools, Policy Editor (Select AI tool -> Allow/Warn/Block), and basic Audit Logs.

**Nice-to-Have "Wow" Features (MVP):**
1. **"Approved Alternatives" Nudging:** When warning/blocking a tool like "Claude", the UI suggests "Use Org ChatGPT Enterprise instead".
2. **Risk Scoring Dashboard:** Automatically categorizes organization risk based on the volume of "High Risk" file-upload tools vs "Low Risk" chat tools.

**Non-Goals for MVP:**
- Directory integration (Active Directory / Okta / Google Workspace syncing).
- Granular departmental policies (MVP will use Org-wide policies).
- Real-time websocket updates (polling is fine).

---

## 4) DATABASE SCHEMA

**Tables:**
1. `organizations`: `id` (PK), `name`, `created_at`
2. `admins`: `id` (PK), `org_id` (FK), `email`, `password_hash`, `role` (Admin/Viewer)
3. `tools_catalog`: `id` (PK), `domain` (e.g., chatgpt.com), `name`, `category` (Chat, Code, Image, File), `base_risk_score` (1-10)
4. `policies`: `id` (PK), `org_id` (FK), `tool_id` (FK), `action` (Allow, Warn, Block), `alternative_tool_id` (FK, optional)
5. `usage_events`: `id` (PK), `org_id` (FK), `tool_id` (FK), `user_hash` (string), `action_taken` (Allowed, Warned, Blocked), `timestamp`
6. `audit_logs`: `id` (PK), `org_id` (FK), `admin_id` (FK), `action` (e.g., "Updated Policy"), `timestamp`

**Indexes & Retention:**
- Indexes on `usage_events(org_id, timestamp)` for fast time-series queries.
- Index on `policies(org_id)` and `tools_catalog(domain)`.
- **Retention Strategy:** Nightly cron deletes `usage_events` older than 30 days.

---

## 5) API SPEC (FastAPI)

**Auth Flow:** Admins login via POST `/auth/login` returning a JWT. Extension uses a static `org_token` (API key) for logging events.

- `POST /api/v1/events` (Extension Endpoint - Auth: `Org-Token`)
  - *Req:* `{"domain": "claude.ai", "user_hash": "a1b2...", "action_taken": "warned", "timestamp": "2023-10-10T..."}`
  - *Res:* `{"status": "recorded"}`

- `GET /api/v1/policy/sync` (Extension Endpoint - Auth: `Org-Token`)
  - *Res:* `{"policies": {"chatgpt.com": {"action": "allow", "alternative": null}, "claude.ai": {"action": "block", "alternative": "chatgpt.com"}}}`

- `GET /api/v1/analytics/top-tools` (Dashboard Endpoint - Auth: JWT)
  - *Res:* `[{"name": "ChatGPT", "count": 1432}]`

- `GET /api/v1/analytics/trends` (Dashboard Endpoint - Auth: JWT)
  - *Purpose:* Time-series usage data for charts.

- `GET /api/v1/policy` | `PUT /api/v1/policy` (Dashboard Endpoint - Auth: JWT)
  - *Purpose:* Admin configuring rules.

- `GET /api/v1/tools` (Dashboard Endpoint - Auth: JWT)
  - *Purpose:* Fetch the master catalog for populating UI dropdowns.

---

## 6) EXTENSION SPEC (Manifest v3)

**Permissions:** `webNavigation`, `storage`, `alarms`, `host_permissions: ["<all_urls>"]`.
**Logic:**
- **Service Worker:** Listens to `chrome.webNavigation.onCommitted`. Parses hostname. Checks against cached `policies` object in `chrome.storage.local`.
- **Actions:** Warn injects banner. Block updates tab URL to local `blocked.html`.
- **Batching:** Offline queue synced every minute via `alarms`.

---

## 7) DASHBOARD SPEC (Next.js)

- **Tech:** Next.js (App Router), Tailwind CSS, shadcn/ui components, Recharts.
- **Pages:** `/login`, `/` (Overview charts), `/policies` (Data table with Select dropdown), `/audit`.
- **State:** React Query for syncing.
- **RBAC:** Middleware checks JWT role (Viewer role greys out save buttons).

---

## 8) SECURITY THREAT MODEL

1. **Spoofing Events:** Malicious user submits fake POST /events. **Mitigation:** `Org-Token` required, rate limiting.
2. **Replay Attacks:** Intercepted API calls re-sent. **Mitigation:** TLS enforced, reject events > 24 hours old.
3. **Extension Tampering:** Employee disables extension. **Mitigation:** Force-installed via Chrome Enterprise Policy.
4. **Privacy Abuse:** Admin trying to trace user. **Mitigation:** Cryptographic one-way hashing of `user_hash`.

---

## 9) IMPLEMENTATION PLAN

- **Week 1:** Setup docker-compose, postgres schema, FastAPI skeleton, static tool catalog.
- **Week 2:** Backend JWT auth, Policy CRUD endpoints, Analytics endpoints.
- **Week 3:** Extension MV3 skeleton, domain detection logic, sync caching via alarms.
- **Week 4:** Extension Warn/Block UI enforcement, push events to backend.
- **Week 5:** Next.js Dashboard UI, Recharts, Policy Editor wiring.
- **Week 6:** Polish, E2E testing, Docker hardening, Demo.
