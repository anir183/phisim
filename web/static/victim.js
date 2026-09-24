"use strict";

const root = document.querySelector("[data-victim-token]");
if (root) {
  const token = root.dataset.victimToken;
  const path = window.location.pathname;
  const isMailList = path === "/mail" || /\/mail\/?$/.test(path);
  const isMessageList = path === "/messages" || /\/messages\/?$/.test(path);
  const listConfig = isMailList
    ? { selector: "#victim-message-list", count: "#victim-unread-count" }
    : isMessageList
      ? { selector: ".conversation-list", count: null }
      : null;
  let lastFingerprint = "";
  let lastStatus = "";

  function notify(message) {
    const toast = document.createElement("div");
    toast.textContent = message;
    toast.className = "victim-toast";
    toast.setAttribute("role", "status");
    document.body.appendChild(toast);
    window.setTimeout(() => toast.remove(), 2600);
  }

  async function refreshList() {
    if (!listConfig) return;
    const target = document.querySelector(listConfig.selector);
    if (!target) return;

    const response = await fetch(path, {
      headers: { Accept: "text/html" },
    });
    if (!response.ok) return;
    const parsed = new DOMParser().parseFromString(
      await response.text(),
      "text/html",
    );
    const incoming = parsed.querySelector(listConfig.selector);
    if (!incoming) return;

    target.replaceChildren(...Array.from(incoming.children));
    if (listConfig.count) {
      const count = parsed.querySelector(listConfig.count);
      const currentCount = document.querySelector(listConfig.count);
      if (count && currentCount) currentCount.textContent = count.textContent;
    }
  }

  async function poll() {
    try {
      const response = await fetch(`/v/${encodeURIComponent(token)}/status`, {
        headers: { Accept: "application/json" },
      });
      if (!response.ok) return;
      const payload = await response.json();
      const fingerprint = JSON.stringify({
        status: payload.status,
        state: payload.state,
      });
      const changed = Boolean(
        lastFingerprint && fingerprint !== lastFingerprint,
      );
      lastFingerprint = fingerprint;
      const previousStatus = lastStatus;
      lastStatus = payload.status;
      if (!changed) return;

      if (previousStatus === "ARMED" && payload.status === "DELIVERED") {
        notify("New message received");
      }
      await refreshList();
    } catch (_error) {
      // The local environment remains usable while the status endpoint recovers.
    }
  }

  window.setInterval(poll, 600);
}
