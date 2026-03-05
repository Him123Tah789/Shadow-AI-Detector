# 🛡️ Shadow AI Detector (Org) — MVP

**Privacy-first, domain-level AI usage monitoring for organizations.**

Detects when employees visit unapproved AI tools (ChatGPT, Claude, Midjourney, etc.) and enforces Allow/Warn/Block policies — without ever capturing prompts, typed text, files, or page content.

## Architecture

| Component | Tech | Port |
|-----------|------|------|
| **Backend API** | Python / FastAPI / SQLAlchemy | `8000` |
| **Database** | PostgreSQL 15 | `5432` |
| **Dashboard** | Next.js 14 / TypeScript / Tailwind / Recharts | `3000` |
| **Extension** | Chrome/Edge Manifest V3 | — |

## Quick Start

### Option A — Docker Compose (recommended)
```bash
cp .env.example .env   # edit secrets as needed
docker-compose up --build
```
- Dashboard → http://localhost:3000
- API docs → http://localhost:8000/docs

### Option B — Local development

**Backend:**
```bash
cd backend
pip install -r requirements.txt
# Make sure PostgreSQL is running locally
export DATABASE_URL=postgresql://shadow_user:shadow_password@localhost/shadow_db
uvicorn main:app --reload
```

**Dashboard:**
```bash
cd dashboard
npm install
npm run dev
```

**Extension:**
1. Open `chrome://extensions` in Chrome or `edge://extensions` in Edge.
2. Enable "Developer mode".
3. Click "Load unpacked" → select the `extension/` folder.
4. Click the extension icon → enter your Org Token (from registration).

## Getting Started

1. Start backend + DB (Docker or local).
2. Open http://localhost:3000/login and **Register** a new org.
3. Note the **Org Token** shown in the dashboard sidebar.
4. Load the browser extension and paste the Org Token into the popup.
5. Visit any AI tool domain → the extension will enforce policies and log events.
6. Configure policies on the Policies page and see analytics populate on Overview.

## Project Structure

```
Shadow AI/
├── backend/
│   ├── main.py            # FastAPI app with all routes
│   ├── models.py          # SQLAlchemy ORM models
│   ├── schemas.py         # Pydantic request/response schemas
│   ├── auth.py            # JWT + password utilities
│   ├── database.py        # DB session management
│   ├── seed.py            # 25 pre-loaded AI tool domains
│   ├── requirements.txt
│   └── Dockerfile
├── dashboard/
│   ├── app/
│   │   ├── login/page.tsx
│   │   ├── dashboard/
│   │   │   ├── page.tsx         # Overview with charts
│   │   │   ├── policies/page.tsx
│   │   │   ├── tools/page.tsx
│   │   │   ├── audit/page.tsx
│   │   │   └── layout.tsx       # Sidebar nav
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── lib/
│   │   ├── api.ts         # API client + auth helpers
│   │   └── hooks.ts       # useApi data fetching hook
│   ├── components/
│   │   └── AuthGuard.tsx
│   ├── Dockerfile
│   └── package.json
├── extension/
│   ├── manifest.json
│   ├── background.js      # Domain detection + policy enforcement
│   ├── popup.html / popup.js
│   ├── blocked.html
│   └── icons/
├── docker-compose.yml
├── .env.example
└── ARCHITECTURE-AND-PLAN.md
```

## Privacy Guarantees

- ✅ Only collects: `domain`, `timestamp`, `org_id`, `user_hash`
- ❌ Never collects: prompts, typed text, clipboard, screenshots, page content, files
- 🔒 User identity is a one-way hash — no emails or names stored in events
- 📅 30-day retention policy (configurable)

## API Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/api/v1/auth/register` | — | Register org + admin |
| POST | `/api/v1/auth/login` | — | Get JWT token |
| POST | `/api/v1/events` | Org-Token | Log single event |
| POST | `/api/v1/events/batch` | Org-Token | Log batch of events |
| GET | `/api/v1/policy/sync` | Org-Token | Extension policy cache |
| GET | `/api/v1/policy` | JWT | List policies |
| PUT | `/api/v1/policy` | JWT (Admin) | Create/update policy |
| DELETE | `/api/v1/policy/{id}` | JWT (Admin) | Remove policy |
| GET | `/api/v1/tools` | JWT | List AI tool catalog |
| GET | `/api/v1/analytics/summary` | JWT | KPI summary |
| GET | `/api/v1/analytics/top-tools` | JWT | Top used tools |
| GET | `/api/v1/analytics/trends` | JWT | Daily usage trend |
| GET | `/api/v1/analytics/risk` | JWT | Risk by category |
| GET | `/api/v1/audit-logs` | JWT | Admin action history |

## License

MIT
