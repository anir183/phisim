"use strict";

const frame = document.querySelector("[data-attack-id]");
if (frame) {
  const attackId = frame.dataset.attackId;
  const sessionId = frame.dataset.sessionId;
  const status = document.getElementById("attack-status");
  const lifecycle = document.getElementById("attack-lifecycle");
  const due = document.getElementById("attack-due");
  const eventCount = document.getElementById("attack-event-count");
  const eventFeed = document.getElementById("attack-events");
  const refreshButton = document.getElementById("refresh-attack");
  const abandonButton = document.getElementById("abandon-attack");
  const victimLink = document.getElementById("victim-link");
  let lastEventsFingerprint = "";
  let refreshInFlight = false;
  let socket = null;
  let reconnectTimer = null;
  let stopped = false;

  function text(value) {
    return typeof value === "string" ? value : JSON.stringify(value);
  }

  function element(tag, value, className) {
    const node = document.createElement(tag);
    node.textContent = text(value);
    if (className) node.className = className;
    return node;
  }

  function eventItem(event) {
    const item = document.createElement("div");
    item.className = "timeline-item";
    item.dataset.eventId = text(event.event_id);
    item.appendChild(element("strong", event.event_type));
    item.appendChild(element("span", event.timestamp, "kicker"));
    item.appendChild(element("span", event.source, "timeline-meta"));
    return item;
  }

  function hasEvent(eventId) {
    return [...eventFeed.children].some(
      (child) => child.dataset.eventId === text(eventId),
    );
  }

  function appendEvent(event) {
    if (!eventFeed || !event || typeof event.event_id !== "string") return;
    if (hasEvent(event.event_id)) return;
    if (eventFeed.querySelector(".empty-state")) eventFeed.replaceChildren();
    eventFeed.appendChild(eventItem(event));
    if (eventCount) {
      const current = Number(eventCount.textContent || "0");
      eventCount.textContent = String(
        Number.isFinite(current) ? current + 1 : 1,
      );
    }
  }

  function renderEvents(events) {
    if (!eventFeed) return;
    eventFeed.replaceChildren();
    if (!Array.isArray(events) || events.length === 0) {
      eventFeed.appendChild(
        element("div", "No events recorded yet.", "empty-state"),
      );
      return;
    }
    for (const event of events) eventFeed.appendChild(eventItem(event));
  }

  async function refresh() {
    if (refreshInFlight) return;
    refreshInFlight = true;
    try {
      const response = await fetch(
        `/api/lab/attacks/${encodeURIComponent(attackId)}?_=${Date.now()}`,
        {
          cache: "no-store",
          headers: { Accept: "application/json" },
        },
      );
      if (!response.ok) throw new Error("Status request failed");
      const payload = await response.json();
      status.textContent = text(payload.status);
      lifecycle.textContent = text(payload.status);
      due.textContent = text(payload.delivery_due_at);
      if (eventCount) {
        eventCount.textContent = text(
          payload.event_count ?? payload.events?.length ?? 0,
        );
      }
      if (victimLink && payload.victim_path) {
        victimLink.href = payload.victim_path;
      }
      const events = Array.isArray(payload.events) ? payload.events : [];
      const eventsFingerprint = JSON.stringify(events);
      if (eventsFingerprint !== lastEventsFingerprint) {
        renderEvents(events);
        lastEventsFingerprint = eventsFingerprint;
      }
    } catch (_error) {
      status.textContent = "Status unavailable";
    } finally {
      refreshInFlight = false;
    }
  }

  function scheduleReconnect() {
    if (stopped || reconnectTimer !== null) return;
    reconnectTimer = window.setTimeout(() => {
      reconnectTimer = null;
      connectLiveEvents();
    }, 2000);
  }

  function connectLiveEvents() {
    if (
      stopped ||
      !sessionId ||
      typeof WebSocket === "undefined" ||
      (socket && socket.readyState <= WebSocket.OPEN)
    ) {
      return;
    }
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    socket = new WebSocket(`${protocol}//${window.location.host}/api/events/ws`);
    socket.addEventListener("message", (message) => {
      try {
        const event = JSON.parse(message.data);
        if (!event || event.session_id !== sessionId) return;
        appendEvent(event);
        void refresh();
      } catch (_error) {
        // Ignore malformed local frames and keep the polling fallback active.
      }
    });
    socket.addEventListener("close", () => {
      socket = null;
      scheduleReconnect();
    });
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
  window.addEventListener("beforeunload", () => {
    stopped = true;
    if (reconnectTimer !== null) window.clearTimeout(reconnectTimer);
    socket?.close();
  });
  void refresh();
  connectLiveEvents();
  window.setInterval(refresh, 1000);
}
