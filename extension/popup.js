document.addEventListener("DOMContentLoaded", () => {
    // Load saved config
    chrome.storage.local.get(["orgToken", "userHash"], (cfg) => {
        if (cfg.orgToken) document.getElementById("orgToken").value = cfg.orgToken;
        if (cfg.userHash) document.getElementById("userHash").value = cfg.userHash;
    });

    // Get live status from service worker
    chrome.runtime.sendMessage({ type: "getStatus" }, (res) => {
        if (res) {
            document.getElementById("policyCount").textContent = res.policyCount;
            document.getElementById("queueCount").textContent = res.queueLength;
            document.getElementById("statusDot").style.background =
                res.policyCount > 0 ? "#4ade80" : "#facc15";
        }
    });

    // Save button
    document.getElementById("saveBtn").addEventListener("click", () => {
        let orgToken = document.getElementById("orgToken").value.trim();
        let userHash = document.getElementById("userHash").value.trim();
        if (!userHash) {
            userHash = "user-" + crypto.randomUUID().slice(0, 12);
            document.getElementById("userHash").value = userHash;
        }
        if (!orgToken) return alert("Organization Token is required.");

        chrome.runtime.sendMessage({ type: "saveConfig", orgToken, userHash }, (res) => {
            if (res && res.ok) {
                const msg = document.getElementById("msg");
                msg.style.display = "block";
                setTimeout(() => (msg.style.display = "none"), 2000);
                // Refresh stats
                chrome.runtime.sendMessage({ type: "getStatus" }, (s) => {
                    if (s) {
                        document.getElementById("policyCount").textContent = s.policyCount;
                        document.getElementById("queueCount").textContent = s.queueLength;
                    }
                });
            }
        });
    });
});
