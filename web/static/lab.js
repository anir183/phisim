"use strict";

const frame = document.querySelector("[data-attack-id]");
if (frame) {
  const attackId = frame.dataset.attackId;
  const status = document.getElementById("attack-status");
  const lifecycle = document.getElementById("attack-lifecycle");
  const due = document.getElementById("attack-due");
  const eventCount = document.getElementById("attack-event-count");
  const refreshButton = document.getElementById("refresh-attack");
  const abandonButton = document.getElementById("abandon-attack");
  const victimLink = document.getElementById("victim-link");

  function text(value) {
    return typeof value === "string" ? value : JSON.stringify(value);
  }

  async function refresh() {
    try {
      const response = await fetch(`/api/lab/attacks/${encodeURIComponent(attackId)}`, {
        headers: { Accept: "application/json" },
      });
      if (!response.ok) throw new Error("Status request failed");
      const payload = await response.json();
      status.textContent = text(payload.status);
      lifecycle.textContent = text(payload.status);
      due.textContent = text(payload.delivery_due_at);
      if (eventCount) eventCount.textContent = text(payload.event_count ?? 0);
      if (victimLink && payload.victim_path) {
        victimLink.href = payload.victim_path;
      }
    } catch (_error) {
      status.textContent = "Status unavailable";
    }
  }

  refreshButton?.addEventListener("click", refresh);
  abandonButton?.addEventListener("click", async () => {
    abandonButton.disabled = true;
    try {
      const response = await fetch(`/api/lab/attacks/${encodeURIComponent(attackId)}/abandon`, {
        method: "POST",
        headers: { Accept: "application/json" },
      });
      if (!response.ok) throw new Error("Abandon failed");
      await refresh();
    } catch (_error) {
      status.textContent = "Abandon unavailable";
      abandonButton.disabled = false;
    }
  });
  window.setInterval(refresh, 1000);
}
