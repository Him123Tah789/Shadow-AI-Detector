# 🛡️ ShieldOps — Shadow AI Detector + Breach Monitor

A combined SaaS MVP with two modules:

| Module | Target | What it does |
|--------|--------|-------------|
| **A — Shadow AI Detector** (B2B) | IT Admins, CISOs | Domain-level detection of unapproved AI tools with allow/warn/block policies. Privacy-first: NEVER captures prompts, text, or files. |
| **B — Breach Monitor + Recovery Kit** (B2C) | Individuals / Employees | Monitor emails for data breaches, get alerts, follow guided step-by-step recovery checklists with progress tracking. NO passwords stored. |

---

## 🚀 Quick Start

### Docker (recommended)

```bash
# 1. Copy env file
cp .env.example .env

# 2. Start everything
docker-compose up --build

# Services:
#   Backend API:  http://localhost:8000
#   Dashboard:    http://localhost:3000
#   PostgreSQL:   localhost:5432
#   Redis:        localhost:6379
```

### Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
# → http://localhost:8000

# Dashboard
cd dashboard
npm install
npm run dev
# → http://localhost:3000

# Worker (background jobs)
cd backend
python worker.py

# Extension
# Load extension/ folder in chrome://extensions (Developer mode)
```

---

## 📁 Project Structure

```
ShieldOps/
├── backend/                  # FastAPI + PostgreSQL
│   ├── main.py              # 30+ API endpoints (auth, events, policy, breach, recovery, score)
│   ├── models.py            # 14 SQLAlchemy tables (6 Module A + 8 Module B)
│   ├── schemas.py           # All Pydantic request/response models
│   ├── auth.py              # JWT + password hashing + RBAC
│   ├── database.py          # DB connection
│   ├── seed.py              # 25 pre-loaded AI tool domains
│   ├── breach_service.py    # Pluggable breach checker (HIBP / Mock)
│   ├── recovery_templates.py# Recovery task templates for 7 platforms
│   ├── notification_service.py # Email + Telegram (stub) notifications
│   ├── crypto_utils.py      # AES-256 email encryption + hashing
│   ├── worker.py            # Background scheduler (breach checks, cleanup, reminders)
│   ├── requirements.txt
│   └── Dockerfile
│
├── dashboard/                # Next.js + Tailwind + Recharts
│   ├── app/
│   │   ├── login/           # Auth page (Org + Personal tabs)
│   │   ├── dashboard/       # Module A: overview, policies, tools, audit
│   │   └── personal/        # Module B: overview, emails, breaches, recovery, score
│   ├── lib/
│   │   ├── api.ts           # Centralized API client (30+ functions)
│   │   └── hooks.ts         # useApi custom hook
│   └── ...
│
├── extension/                # Chrome/Edge MV3 Extension
│   ├── manifest.json
│   ├── background.js        # Domain detection, policy caching, event queue
│   ├── popup.html/js        # Config UI
│   └── blocked.html         # Block page
│
├── docker-compose.yml        # PostgreSQL + Redis + Backend + Worker + Dashboard
├── .env.example
└── ARCHITECTURE-AND-PLAN.md
```

---

## 🔌 API Endpoints

### Module A — Shadow AI Detector

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/v1/auth/register` | Register org admin |
| `POST` | `/api/v1/auth/login` | Login org admin |
| `POST` | `/api/v1/events` | Record usage event (extension) |
| `POST` | `/api/v1/events/batch` | Batch record events |
| `GET` | `/api/v1/policy/sync` | Get policies for extension |
| `GET/PUT/DEL` | `/api/v1/policy` | Policy CRUD |
| `GET` | `/api/v1/tools` | Tool catalog |
| `GET` | `/api/v1/analytics/*` | Summary, top-tools, trends, risk |
| `GET` | `/api/v1/audit-logs` | Admin action history |

### Module B — Breach Monitor + Recovery Kit

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/v1/personal/auth/register` | Register personal user |
| `POST` | `/api/v1/personal/auth/login` | Login personal user |
| `POST` | `/api/v1/breach/monitor-email` | Add email to monitor |
| `GET` | `/api/v1/breach/monitored-emails` | List monitored emails |
| `DELETE` | `/api/v1/breach/monitored-email/{id}` | Remove email |
| `GET` | `/api/v1/breach/status` | Get all breaches |
| `POST` | `/api/v1/breach/run-check` | Trigger breach check |
| `GET` | `/api/v1/recovery/platforms` | List supported platforms |
| `POST` | `/api/v1/recovery/plan` | Create recovery plan |
| `GET` | `/api/v1/recovery/plans` | List all plans |
| `GET` | `/api/v1/recovery/plan/{id}` | Get plan detail |
| `PATCH` | `/api/v1/recovery/task/{id}` | Toggle task completion |
| `GET` | `/api/v1/security-score` | Get security score |
| `GET` | `/api/v1/security-score/history` | Score history |

---

## 🔒 Privacy & Security

- **Module A**: Only stores `domain`, `timestamp`, `org_id`, `user_hash` — NEVER prompts, text, or files
- **Module B**: Emails encrypted with AES-256-GCM at rest. NO passwords stored. Only task completion timestamps tracked.
- **User hashing**: SHA-256 one-way hash — irreversible
- **JWT auth**: 24h expiry, HMAC-SHA256
- **RBAC**: Admin/Viewer roles (org), personal user isolation (breach monitor)
- **Replay protection**: Events >24h old are rejected
- **Retention**: Usage events auto-deleted after 30 days

---

## 🔧 Configuration

See `.env.example` for all environment variables. Key settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `BREACH_CHECKER` | `mock` | `mock` for testing, `hibp` for real HIBP API |
| `HIBP_API_KEY` | — | Required if `BREACH_CHECKER=hibp` ($3.50/mo) |
| `ENCRYPTION_KEY` | auto-gen | 32-byte base64 key for email encryption |
| `SMTP_HOST` | — | SMTP server for email notifications |

---

## 💰 Monetization

| Module | Model | Pricing |
|--------|-------|---------|
| **A — Shadow AI** | B2B per-seat | $1–$3/user/month |
| **B — Breach Monitor** | Freemium | 1 email free → paid for more |
