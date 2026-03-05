# Shadow AI Monitoring: Real-Life Implementation Plan

This document outlines the specific changes required to implement the "industry-style" test plan, ensuring the Shadow AI Monitor behaves like a production-ready enterprise security tool.

## Target Goals

1. **Extended Event Metadata**: Capture `device_id_hash`, `browser`, `extension_version`, etc., from the Chrome extension and save them to the database.
2. **Automated Alerts**: Generate SOC alerts (`SpikeUsage`, `HighRiskToolAccess`) directly in the backend during event ingestion.
3. **Comprehensive Audit Logs**: Ensure all admin actions (Policy Create/Update/Delete) generate detailed, non-repudiable audit logs.
4. **Offline Resilience**: Ensure the extension queue can gracefully hand off batched events and retry if the network drops.
5. **Dashboard Export**: Provide an endpoint and UI to export compliance data as CSV.

---

## Proposed Changes

### Extension (Telemetry & Enforcement)
*   **[MODIFY] [extension/background.js](file:///c:/Users/Faishal/Downloads/Shadow%20AI/extension/background.js)**
    *   Add a helper to generate a stable, anonymous `deviceHash` (e.g., random UUID stored in `chrome.storage.local`).
    *   Extract `browser` string (from `navigator.userAgent`) and `extension_version` (from `chrome.runtime.getManifest().version`).
    *   Update [handlePolicy()](file:///c:/Users/Faishal/Downloads/Shadow%20AI/extension/background.js#79-111) to push these new metadata fields into the `eventQueue` payload.
    *   Ensure [flushQueue](file:///c:/Users/Faishal/Downloads/Shadow%20AI/extension/background.js#134-153) only removes events upon a `201 OK` response to guarantee offline resilience.

### Backend (API & Processing)
*   **[MODIFY] [backend/main.py](file:///c:/Users/Faishal/Downloads/Shadow%20AI/backend/main.py)**
    *   **Event Ingestion (`/api/v1/events` & `/api/v1/events/batch`)**:
        *   Extract the new fields (`device_id_hash`, `browser`, `extension_version`, `category`, `tool_name`) from the payload and insert them into the [UsageEvent](file:///c:/Users/Faishal/Downloads/Shadow%20AI/backend/models.py#61-83) model.
        *   Implement **Alert Logic**:
            *   *HighRiskToolAccess*: Check the tool's `base_risk_score`. If > 7, generate an [AlertEvent](file:///c:/Users/Faishal/Downloads/Shadow%20AI/backend/models.py#101-115) (High severity).
            *   *SpikeUsage*: Query the DB for the user's event count over the last 10 minutes. If > 20, generate an [AlertEvent](file:///c:/Users/Faishal/Downloads/Shadow%20AI/backend/models.py#101-115) (Medium severity).
    *   **Audit Logs**: Update `/api/v1/policy` (`PUT` and `DELETE`) to properly log complete `before/after` states into the [AuditLog](file:///c:/Users/Faishal/Downloads/Shadow%20AI/backend/models.py#85-99) table, capturing Admin IP (if available) and User Agent.
    *   **Export (`/api/v1/analytics/export`)**: Create a new endpoint that queries recent `UsageEvents` and returns a formatted CSV response.
    *   **Alerts Retrieval (`/api/v1/alerts`)**: Create a new endpoint to fetch recent SOC alerts for the dashboard.

### Dashboard (UI/Analytics)
*   **[NEW] `dashboard/app/dashboard/alerts/page.tsx`**
    *   Create a simple table page to view active SOC alerts.
*   **[MODIFY] [dashboard/app/dashboard/audit/page.tsx](file:///c:/Users/Faishal/Downloads/Shadow%20AI/dashboard/app/dashboard/audit/page.tsx)**
    *   Ensure the audit logs view correctly parses the JSON details and displays the admin action.
*   **[MODIFY] [dashboard/app/dashboard/page.tsx](file:///c:/Users/Faishal/Downloads/Shadow%20AI/dashboard/app/dashboard/page.tsx)**
    *   Add an "Export to CSV" button that calls the backend export API.

---

## Verification Plan

### Automated Tests
1. No dedicated pytest logic was requested for this prompt, but the changes will map perfectly to the requested "Real-Life Industry Test Plan".

### Manual Verification
1.  **Baseline & Extension Parsing**:
    *   Clear extension storage, reload the extension, and navigate to `chatgpt.com`.
    *   Check [shieldops.db](file:///c:/Users/Faishal/Downloads/Shadow%20AI/backend/shieldops.db) [UsageEvent](file:///c:/Users/Faishal/Downloads/Shadow%20AI/backend/models.py#61-83) table. Confirm `device_id_hash`, `browser`, and `extension_version` are populated.
2.  **Alerts Testing**:
    *   Spam-refresh an AI tool 25 times in under 2 minutes. Verify an [AlertEvent](file:///c:/Users/Faishal/Downloads/Shadow%20AI/backend/models.py#101-115) (SpikeUsage) is created.
    *   Navigate to a high-risk tool (e.g., `gamma.app`). Verify an [AlertEvent](file:///c:/Users/Faishal/Downloads/Shadow%20AI/backend/models.py#101-115) (HighRisk) is created.
3.  **Audit Testing**:
    *   Change a policy via the dashboard. Verify [AuditLog](file:///c:/Users/Faishal/Downloads/Shadow%20AI/backend/models.py#85-99) row possesses deep change state details.
4.  **Offline Resilience**:
    *   Disable network, browse 3 sites (they should block/warn as appropriate locally).
    *   Enable network, wait 1 minute. Verify events arrive in the DB without drops.
5.  **Export Testing**:
    *   Click "Export CSV" on the Dashboard and confirm the downloaded CSV opens cleanly.

