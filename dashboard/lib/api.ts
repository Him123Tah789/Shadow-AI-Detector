const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

function getHeaders(): HeadersInit {
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    const h: any = { "Content-Type": "application/json" };
    if (token) h["Authorization"] = `Bearer ${token}`;
    return h;
}

async function apiFetch(path: string, opts: RequestInit = {}) {
    const res = await fetch(`${API_URL}${path}`, {
        ...opts,
        headers: { ...getHeaders(), ...(opts.headers || {}) },
    });
    if (res.status === 401) {
        if (typeof window !== "undefined") {
            localStorage.removeItem("token");
            window.location.href = "/login";
        }
        throw new Error("Unauthorized");
    }
    if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || res.statusText);
    }
    return res.json();
}

// ══════════════════════════════════════════════════
//  AUTH — Org (Module A)
// ══════════════════════════════════════════════════

export async function login(email: string, password: string) {
    const data = await apiFetch("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
    });
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("role", data.role);
    localStorage.setItem("org_id", String(data.org_id));
    localStorage.setItem("org_token", data.org_token);
    localStorage.setItem("auth_type", "org");
    return data;
}

export async function register(email: string, password: string, org_name: string) {
    const data = await apiFetch("/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password, org_name }),
    });
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("role", data.role);
    localStorage.setItem("org_id", String(data.org_id));
    localStorage.setItem("org_token", data.org_token);
    localStorage.setItem("auth_type", "org");
    return data;
}

// ══════════════════════════════════════════════════
//  AUTH — Personal (Module B)
// ══════════════════════════════════════════════════

export async function personalLogin(email: string, password: string) {
    const data = await apiFetch("/personal/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
    });
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("auth_type", "personal");
    localStorage.setItem("user_id", String(data.user_id));
    localStorage.setItem("tier", data.tier);
    localStorage.setItem("max_emails", String(data.max_emails));
    return data;
}

export async function personalRegister(email: string, password: string) {
    const data = await apiFetch("/personal/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password }),
    });
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("auth_type", "personal");
    localStorage.setItem("user_id", String(data.user_id));
    localStorage.setItem("tier", data.tier);
    localStorage.setItem("max_emails", String(data.max_emails));
    return data;
}

// ── Shared Auth Helpers ─────────────────────────

export function logout() {
    localStorage.clear();
    window.location.href = "/login";
}

export function isLoggedIn() {
    return typeof window !== "undefined" && !!localStorage.getItem("token");
}

export function getRole() {
    return typeof window !== "undefined" ? localStorage.getItem("role") || "viewer" : "viewer";
}

export function getOrgToken() {
    return typeof window !== "undefined" ? localStorage.getItem("org_token") || "" : "";
}

export function getAuthType() {
    return typeof window !== "undefined" ? localStorage.getItem("auth_type") || "org" : "org";
}

export function getTier() {
    return typeof window !== "undefined" ? localStorage.getItem("tier") || "free" : "free";
}

// ══════════════════════════════════════════════════
//  MODULE A — Analytics, Policy, Tools, Audit
// ══════════════════════════════════════════════════

export const fetchSummary = () => apiFetch("/analytics/summary");
export const fetchTopTools = (days = 30) => apiFetch(`/analytics/top-tools?days=${days}`);
export const fetchTrends = (days = 30) => apiFetch(`/analytics/trends?days=${days}`);
export const fetchRisk = () => apiFetch("/analytics/risk");

export const fetchPolicies = () => apiFetch("/policy");
export const upsertPolicy = (body: { tool_id: number; action: string; alternative_tool_id?: number | null }) =>
    apiFetch("/policy", { method: "PUT", body: JSON.stringify(body) });
export const deletePolicy = (id: number) => apiFetch(`/policy/${id}`, { method: "DELETE" });

export const fetchTools = () => apiFetch("/tools");
export const fetchAuditLogs = (limit = 50) => apiFetch(`/audit-logs?limit=${limit}`);
export const fetchAlerts = (limit = 50) => apiFetch(`/alerts?limit=${limit}`);

// ══════════════════════════════════════════════════
//  MODULE B — Breach Monitor
// ══════════════════════════════════════════════════

export const addMonitoredEmail = (email: string, label?: string) =>
    apiFetch("/breach/monitor-email", {
        method: "POST",
        body: JSON.stringify({ email, label }),
    });

export const fetchMonitoredEmails = () => apiFetch("/breach/monitored-emails");

export const removeMonitoredEmail = (id: number) =>
    apiFetch(`/breach/monitored-email/${id}`, { method: "DELETE" });

export const fetchBreachStatus = () => apiFetch("/breach/status");

export const runBreachCheck = (monitored_email_id: number) =>
    apiFetch("/breach/run-check", {
        method: "POST",
        body: JSON.stringify({ monitored_email_id }),
    });

// ══════════════════════════════════════════════════
//  MODULE B — Recovery Kit
// ══════════════════════════════════════════════════

export const fetchPlatforms = () => apiFetch("/recovery/platforms");

export const createRecoveryPlan = (platform: string, breach_event_id?: number) =>
    apiFetch("/recovery/plan", {
        method: "POST",
        body: JSON.stringify({ platform, breach_event_id }),
    });

export const fetchRecoveryPlans = () => apiFetch("/recovery/plans");

export const fetchRecoveryPlan = (planId: number) => apiFetch(`/recovery/plan/${planId}`);

export const updateRecoveryTask = (taskId: number, is_completed: boolean) =>
    apiFetch(`/recovery/task/${taskId}`, {
        method: "PATCH",
        body: JSON.stringify({ is_completed }),
    });

// ══════════════════════════════════════════════════
//  MODULE B — Security Score
// ══════════════════════════════════════════════════

export const fetchSecurityScore = () => apiFetch("/security-score");

export const fetchScoreHistory = (limit = 12) => apiFetch(`/security-score/history?limit=${limit}`);
