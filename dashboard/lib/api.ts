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

// ── Auth ─────────────────────────────────────────
export async function login(email: string, password: string) {
    const data = await apiFetch("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
    });
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("role", data.role);
    localStorage.setItem("org_id", String(data.org_id));
    localStorage.setItem("org_token", data.org_token);
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
    return data;
}

export function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    localStorage.removeItem("org_id");
    localStorage.removeItem("org_token");
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

// ── Analytics ────────────────────────────────────
export const fetchSummary = () => apiFetch("/analytics/summary");
export const fetchTopTools = (days = 30) => apiFetch(`/analytics/top-tools?days=${days}`);
export const fetchTrends = (days = 30) => apiFetch(`/analytics/trends?days=${days}`);
export const fetchRisk = () => apiFetch("/analytics/risk");

// ── Policy ───────────────────────────────────────
export const fetchPolicies = () => apiFetch("/policy");
export const upsertPolicy = (body: { tool_id: number; action: string; alternative_tool_id?: number | null }) =>
    apiFetch("/policy", { method: "PUT", body: JSON.stringify(body) });
export const deletePolicy = (id: number) => apiFetch(`/policy/${id}`, { method: "DELETE" });

// ── Tools ────────────────────────────────────────
export const fetchTools = () => apiFetch("/tools");

// ── Audit ────────────────────────────────────────
export const fetchAuditLogs = (limit = 50) => apiFetch(`/audit-logs?limit=${limit}`);
