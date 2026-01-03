async function refreshStatus() {
    try {
        const response = await fetch("/api/status");
        const data = await response.json();

        const statusEl = document.getElementById("bot-status");

        if (data.online) {
            statusEl.textContent = "ONLINE";
            statusEl.className = "status-online";
        } else {
            statusEl.textContent = "OFFLINE";
            statusEl.className = "status-offline";
        }
    } catch (err) {
        console.error("Failed to fetch bot status", err);
    }
}

// Refresh every 5 seconds
setInterval(refreshStatus, 5000);

// Run once immediately on page load
refreshStatus();