// ─────────────────────────────────────────────────
// Shadow AI Detector — Service Worker  (MV3)
// Privacy-first: only domain + timestamp + user_hash
// ─────────────────────────────────────────────────

const API_BASE = "http://localhost:8000/api/v1";
let policyCache = {};   // { "chatgpt.com": { action:"warn", alternative:"..." } }
let eventQueue = [];   // offline batch queue

// ── Config stored in chrome.storage.local ─────────
async function getConfig() {
    return new Promise((resolve) => {
        chrome.storage.local.get(["orgToken", "userHash", "policies"], (r) => {
            resolve({
                orgToken: r.orgToken || "",
                userHash: r.userHash || "",
                policies: r.policies || {},
            });
        });
    });
}

// ── Startup ───────────────────────────────────────
chrome.runtime.onInstalled.addListener(async () => {
    const cfg = await getConfig();
    policyCache = cfg.policies;
    if (cfg.orgToken) syncPolicies(cfg.orgToken);

    // Sync every 15 min, flush events every 1 min
    chrome.alarms.create("syncPolicies", { periodInMinutes: 15 });
    chrome.alarms.create("flushEvents", { periodInMinutes: 1 });
});

chrome.runtime.onStartup.addListener(async () => {
    const cfg = await getConfig();
    policyCache = cfg.policies;
    if (cfg.orgToken) syncPolicies(cfg.orgToken);
});

chrome.alarms.onAlarm.addListener(async (alarm) => {
    const cfg = await getConfig();
    if (alarm.name === "syncPolicies" && cfg.orgToken) syncPolicies(cfg.orgToken);
    if (alarm.name === "flushEvents" && cfg.orgToken) flushQueue(cfg.orgToken);
});

// ── Policy sync ───────────────────────────────────
async function syncPolicies(orgToken) {
    try {
        const res = await fetch(`${API_BASE}/policy/sync`, {
            headers: { "org-token": orgToken },
        });
        if (res.ok) {
            const data = await res.json();
            policyCache = data.policies || {};
            chrome.storage.local.set({ policies: policyCache });
        }
    } catch (_) {
        // Offline — keep existing cache
    }
}

// ── Domain detection ──────────────────────────────
chrome.webNavigation.onCommitted.addListener(async (details) => {
    if (details.frameId !== 0) return;
    try {
        const url = new URL(details.url);
        if (!url.hostname) return;
        const domain = url.hostname.replace(/^www\./, "");

        if (policyCache[domain]) {
            const cfg = await getConfig();
            if (!cfg.orgToken) return;
            const policy = policyCache[domain];
            handlePolicy(domain, policy, details.tabId, cfg);
        }
    } catch (_) { /* ignore chrome:// etc. */ }
});

// ── Enforcement ───────────────────────────────────
function handlePolicy(domain, policy, tabId, cfg) {
    const action = policy.action || "allow";

    if (action === "block") {
        const alt = policy.alternative || "";
        const blockUrl = chrome.runtime.getURL(
            `blocked.html?domain=${encodeURIComponent(domain)}&alt=${encodeURIComponent(alt)}`
        );
        chrome.tabs.update(tabId, { url: blockUrl });
    }

    if (action === "warn") {
        const alt = policy.alternative || "";
        chrome.scripting.executeScript({
            target: { tabId },
            func: showWarnBanner,
            args: [domain, alt],
        }).catch(() => { });
    }

    // Queue event (never captures page content — only domain)
    eventQueue.push({
        domain,
        user_hash: cfg.userHash,
        action_taken: action,
        timestamp: new Date().toISOString(),
    });

    // Immediate flush attempt if queue has 5+ items
    if (eventQueue.length >= 5) flushQueue(cfg.orgToken);
}

// ── Warning banner (injected into page) ──────────
function showWarnBanner(domain, alternative) {
    if (document.getElementById("__shadow_ai_warn")) return;
    const bar = document.createElement("div");
    bar.id = "__shadow_ai_warn";
    bar.style.cssText = `
    position: fixed; top: 0; left: 0; right: 0; z-index: 2147483647;
    background: linear-gradient(135deg, #ff9800, #f44336); color: #fff;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 14px; padding: 12px 24px;
    display: flex; align-items: center; justify-content: space-between;
    box-shadow: 0 2px 12px rgba(0,0,0,.25);
  `;
    let msg = `⚠️  <b>${domain}</b> is NOT an approved AI tool in your organization.`;
    if (alternative) msg += `  Recommended: <b>${alternative}</b>`;
    const close = `<button onclick="this.parentElement.remove()" style="
    background:rgba(255,255,255,.25);border:none;color:#fff;border-radius:4px;
    padding:4px 12px;cursor:pointer;font-size:13px;margin-left:16px;">Dismiss</button>`;
    bar.innerHTML = msg + close;
    document.body.prepend(bar);
}

// ── Event batching & retry ────────────────────────
async function flushQueue(orgToken) {
    if (!eventQueue.length || !orgToken) return;
    const batch = eventQueue.splice(0, 50);      // max 50 per flush
    try {
        const res = await fetch(`${API_BASE}/events/batch`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "org-token": orgToken,
            },
            body: JSON.stringify(batch),
        });
        if (!res.ok) throw new Error(res.status);
    } catch (_) {
        // Push back for retry on next alarm tick
        eventQueue.unshift(...batch);
    }
}

// ── Message handler (popup → service worker) ─────
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg.type === "getStatus") {
        sendResponse({
            policyCount: Object.keys(policyCache).length,
            queueLength: eventQueue.length,
        });
    }
    if (msg.type === "saveConfig") {
        chrome.storage.local.set({
            orgToken: msg.orgToken,
            userHash: msg.userHash,
        }, () => {
            syncPolicies(msg.orgToken);
            sendResponse({ ok: true });
        });
        return true; // async response
    }
});
