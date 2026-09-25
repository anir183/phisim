"use strict";

const root = document.querySelector("[data-victim-token]");
if (root) {
  const token = root.dataset.victimToken;
  const path = window.location.pathname;
  const requestPath = `${path}${window.location.search}`;
  const isMailList = path === "/mail" || /\/mail\/?$/.test(path);
  const isMessageList = path === "/messages" || /\/messages\/?$/.test(path);
  const listConfig = isMailList
    ? { selectors: ["#victim-message-list"], count: "#victim-unread-count" }
    : isMessageList
      ? { selectors: [".quickchat-thread-list", ".conversation-list"], count: null }
      : null;
  let lastFingerprint = "";
  let lastStatus = "";
  let pollInFlight = false;

  function notify(message) {
    const toast = document.createElement("div");
    toast.textContent = message;
    toast.className = "victim-toast";
    toast.setAttribute("role", "status");
    document.body.appendChild(toast);
    window.setTimeout(() => toast.remove(), 2600);
  }

  function listTarget() {
    if (!listConfig) return null;
    for (const selector of listConfig.selectors) {
      const target = document.querySelector(selector);
      if (target) return target;
    }
    return null;
  }

  async function refreshList() {
    const target = listTarget();
    if (!target) return;
    const selector = listConfig.selectors.find((item) => document.querySelector(item));
    const response = await fetch(requestPath, {
      cache: "no-store",
      headers: { Accept: "text/html" },
    });
    if (!response.ok) return;
    const parsed = new DOMParser().parseFromString(
      await response.text(),
      "text/html",
    );
    const incoming = parsed.querySelector(selector);
    if (!incoming) return;

    target.replaceChildren(...Array.from(incoming.children));
    if (listConfig.count) {
      const count = parsed.querySelector(listConfig.count);
      const currentCount = document.querySelector(listConfig.count);
      if (count && currentCount) currentCount.textContent = count.textContent;
    }
  }

  async function poll() {
    if (pollInFlight) return;
    pollInFlight = true;
    try {
      const response = await fetch(
        `/v/${encodeURIComponent(token)}/status?_=${Date.now()}`,
        {
          cache: "no-store",
          headers: { Accept: "application/json" },
        },
      );
      if (!response.ok) return;
      const payload = await response.json();
      const fingerprint = JSON.stringify({
        status: payload.status,
        state: payload.state,
      });
      const changed = !lastFingerprint || fingerprint !== lastFingerprint;
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
    } finally {
      pollInFlight = false;
    }
  }

  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) void poll();
  });
  window.setInterval(poll, 600);
}
