"use strict";

const state = {
  sessions: [],
  selectedSession: "",
  events: new Map(),
  indicators: new Map(),
  selectedEvent: "",
  socket: null,
  reconnectTimer: null,
  retryAttempt: 0,
  stopped: false,
  sessionsInitialized: false,
  sessionsRefreshInFlight: false,
};

const sessionFilter = document.getElementById("session-filter");
const channelFilter = document.getElementById("channel-filter");
const indicatorFilter = document.getElementById("indicator-filter");
const sessionList = document.getElementById("session-list");
const sessionCount = document.getElementById("session-count");
const timeline = document.getElementById("timeline");
const eventCount = document.getElementById("event-count");
const detail = document.getElementById("event-detail");
const connectionState = document.getElementById("connection-state");
const refreshButton = document.getElementById("refresh-console");
const clearButton = document.getElementById("clear-console");

function text(value) {
  if (typeof value === "string") return value;
  if (value === null || value === undefined) return "";
  return JSON.stringify(value);
}

function element(tag, value, className) {
  const node = document.createElement(tag);
  node.textContent = text(value);
  if (className) node.className = className;
  return node;
}

function setConnection(label, tone) {
  connectionState.replaceChildren(element("span", label, `badge badge-${tone}`));
}

function showEmpty(parent, message) {
  parent.replaceChildren(element("div", message, "empty-state"));
}

async function getJson(url) {
  const response = await fetch(url, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  return response.json();
}

function channelFor(event) {
  return event.metadata && typeof event.metadata.channel === "string"
    ? event.metadata.channel
    : "other";
}

function renderSessions() {
  sessionFilter.replaceChildren();
  const placeholder = document.createElement("option");
  placeholder.value = "";
  placeholder.textContent = "Choose a session";
  sessionFilter.appendChild(placeholder);
  for (const session of state.sessions) {
    const option = document.createElement("option");
    option.value = session.session_id;
    option.textContent = `${session.session_id.slice(0, 8)} · ${session.status}`;
    option.selected = session.session_id === state.selectedSession;
    sessionFilter.appendChild(option);
  }
  sessionCount.textContent = String(state.sessions.length);
  sessionList.replaceChildren();
  if (state.sessions.length === 0) {
    showEmpty(sessionList, "No Sessions are available yet.");
    return;
  }
  for (const session of state.sessions) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "session-item";
    button.setAttribute("aria-current", String(session.session_id === state.selectedSession));
    button.appendChild(element("strong", session.session_id.slice(0, 12)));
    button.appendChild(element("span", `${session.scenario_id} · ${session.status}`));
    button.appendChild(element("span", session.started_at || ""));
    button.addEventListener("click", () => selectSession(session.session_id));
    sessionList.appendChild(button);
  }
}

function rememberLiveSession(event) {
  if (!event || typeof event.session_id !== "string") return;
  const existing = state.sessions.find(
    (session) => session.session_id === event.session_id,
  );
  if (!existing) {
    state.sessions.push({
      session_id: event.session_id,
      scenario_id: event.scenario_id || "unknown",
      started_at: event.timestamp || "",
      completed_at: null,
      status: "active",
    });
  }
  if (!state.selectedSession) {
    state.selectedSession = event.session_id;
    state.events.clear();
    state.indicators.clear();
    state.selectedEvent = "";
  }
  renderSessions();
}

function renderIndicatorFilter() {
  const current = indicatorFilter.value;
  const codes = new Set();
  for (const indicators of state.indicators.values()) {
    for (const indicator of indicators) {
      if (indicator && typeof indicator.code === "string") codes.add(indicator.code);
    }
  }
  indicatorFilter.replaceChildren();
  const all = document.createElement("option");
  all.value = "";
  all.textContent = "All indicators";
  indicatorFilter.appendChild(all);
  for (const code of [...codes].sort()) {
    const option = document.createElement("option");
    option.value = code;
    option.textContent = code.replaceAll("_", " ");
    option.selected = code === current;
    indicatorFilter.appendChild(option);
  }
}

function visibleEvents() {
  const channel = channelFilter.value;
  const indicator = indicatorFilter.value;
  return [...state.events.values()]
    .filter((event) => !channel || channelFor(event) === channel)
    .filter((event) => {
      if (!indicator) return true;
      return (state.indicators.get(event.event_id) || event.indicators || []).some(
        (item) => item && item.code === indicator,
      );
    })
    .sort((left, right) => {
      const leftTime = Date.parse(left.timestamp || "") || 0;
      const rightTime = Date.parse(right.timestamp || "") || 0;
      return rightTime - leftTime;
    });
}

function renderTimeline() {
  const events = visibleEvents();
  timeline.replaceChildren();
  eventCount.textContent = `${events.length} event${events.length === 1 ? "" : "s"}`;
  if (events.length === 0) {
    showEmpty(
      timeline,
      state.selectedSession ? "No Events match these filters." : "Select a session to inspect its timeline.",
    );
    renderDetail();
    return;
  }
  for (const event of events) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "timeline-item";
    button.setAttribute("aria-current", String(event.event_id === state.selectedEvent));
    button.appendChild(element("strong", event.event_type));
    button.appendChild(element("span", event.timestamp || ""));
    const meta = document.createElement("span");
    meta.className = "timeline-meta";
    meta.appendChild(element("span", event.scenario_id || ""));
    meta.appendChild(element("span", channelFor(event)));
    for (const indicator of state.indicators.get(event.event_id) || event.indicators || []) {
      if (indicator && typeof indicator.code === "string") {
        meta.appendChild(element("span", indicator.code.replaceAll("_", " "), "indicator-chip"));
      }
    }
    button.appendChild(meta);
    button.addEventListener("click", () => {
      state.selectedEvent = event.event_id;
      renderTimeline();
      renderDetail();
    });
    timeline.appendChild(button);
  }
  renderDetail();
}

function renderDetail() {
  const event = state.events.get(state.selectedEvent);
  detail.replaceChildren();
  if (!event) {
    showEmpty(detail, "Select an Event to see its evidence.");
    return;
  }
  detail.appendChild(element("h3", event.event_type));
  detail.appendChild(element("p", `${event.scenario_id} · ${event.session_id}`));
  const indicators = state.indicators.get(event.event_id) || event.indicators || [];
  if (indicators.length > 0) {
    const heading = element("h3", "Indicators");
    heading.style.marginTop = "1rem";
    detail.appendChild(heading);
    for (const indicator of indicators) {
      if (!indicator || typeof indicator.code !== "string") continue;
      const block = document.createElement("div");
      block.className = "evidence-list";
      const item = document.createElement("li");
      item.appendChild(element("strong", indicator.code.replaceAll("_", " ")));
      item.appendChild(element("span", indicator.evidence || "No evidence text supplied."));
      item.appendChild(element("p", indicator.explanation || ""));
      block.appendChild(item);
      detail.appendChild(block);
    }
  }
  const metadata = document.createElement("pre");
  metadata.textContent = JSON.stringify(event.metadata || {}, null, 2);
  detail.appendChild(metadata);
}

async function loadSessions(force = false) {
  if (state.sessionsRefreshInFlight) return;
  state.sessionsRefreshInFlight = true;
  try {
    const sessions = await getJson("/api/sessions");
    if (!Array.isArray(sessions)) throw new Error("Unexpected Session response");
    const fetchedIds = new Set(sessions.map((session) => session.session_id));
    const liveOnlySessions = state.sessions.filter(
      (session) => !fetchedIds.has(session.session_id),
    );
    state.sessions = [...sessions, ...liveOnlySessions];
    const previousSelection = state.selectedSession;
    if (!state.selectedSession && state.sessions.length > 0) {
      state.selectedSession = state.sessions[state.sessions.length - 1].session_id;
    } else if (
      state.selectedSession &&
      !state.sessions.some((session) => session.session_id === state.selectedSession)
    ) {
      state.selectedSession = state.sessions[0]?.session_id || "";
    }
    renderSessions();
    const shouldRefreshSelection =
      force || !state.sessionsInitialized || !previousSelection;
    state.sessionsInitialized = true;
    if (state.selectedSession && (shouldRefreshSelection || previousSelection)) {
      await selectSession(state.selectedSession, !force && !!previousSelection);
    }
  } catch (_error) {
    showEmpty(sessionList, "Unable to load Sessions.");
    setConnection("API error", "danger");
  } finally {
    state.sessionsRefreshInFlight = false;
  }
}

async function selectSession(sessionId, preserve = false) {
  state.selectedSession = sessionId;
  if (!preserve) {
    state.events.clear();
    state.indicators.clear();
    state.selectedEvent = "";
  }
  renderSessions();
  renderTimeline();
  if (!sessionId) return;
  setConnection("Loading", "warning");
  try {
    const encoded = encodeURIComponent(sessionId);
    const [events, analysis] = await Promise.all([
      getJson(`/api/events?session_id=${encoded}`),
      getJson(`/api/analysis/sessions/${encoded}`),
    ]);
    if (!Array.isArray(events) || !analysis || !Array.isArray(analysis.timeline)) {
      throw new Error("Unexpected Event response");
    }
    for (const entry of analysis.timeline) {
      if (entry && typeof entry.event_id === "string") {
        state.indicators.set(entry.event_id, entry.indicators || []);
      }
    }
    for (const event of events) {
      if (event && typeof event.event_id === "string") {
        state.events.set(event.event_id, event);
      }
    }
    renderIndicatorFilter();
    renderTimeline();
    setConnection("Live", "success");
  } catch (_error) {
    showEmpty(timeline, "Unable to load this Session.");
    setConnection("Session error", "danger");
  }
}

async function refreshLiveIndicators(event) {
  if (!state.selectedSession || event.session_id !== state.selectedSession) return;
  try {
    const encoded = encodeURIComponent(state.selectedSession);
    const analysis = await getJson(`/api/analysis/sessions/${encoded}`);
    const entry = Array.isArray(analysis.timeline)
      ? analysis.timeline.find((item) => item && item.event_id === event.event_id)
      : null;
    if (entry && Array.isArray(entry.indicators)) {
      state.indicators.set(event.event_id, entry.indicators);
      renderIndicatorFilter();
      renderTimeline();
    }
  } catch (_error) {
    setConnection("Live; analysis pending", "warning");
  }
}

function rememberLiveEvent(event) {
  if (!event || typeof event.event_id !== "string") return;
  rememberLiveSession(event);
  if (state.selectedSession && event.session_id !== state.selectedSession) return;
  state.events.set(event.event_id, event);
  if (Array.isArray(event.indicators)) state.indicators.set(event.event_id, event.indicators);
  renderIndicatorFilter();
  renderTimeline();
  void refreshLiveIndicators(event);
}

function scheduleReconnect() {
  if (state.stopped || state.reconnectTimer !== null) return;
  if (state.retryAttempt >= 8) {
    setConnection("Offline", "danger");
    return;
  }
  const delay = Math.min(30000, 1000 * (2 ** state.retryAttempt));
  state.retryAttempt += 1;
  state.reconnectTimer = window.setTimeout(() => {
    state.reconnectTimer = null;
    connect();
  }, delay);
}

function connect() {
  if (state.stopped) return;
  if (state.socket && (state.socket.readyState === WebSocket.OPEN || state.socket.readyState === WebSocket.CONNECTING)) return;
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const socket = new WebSocket(`${protocol}//${window.location.host}/api/events/ws`);
  state.socket = socket;
  socket.addEventListener("open", () => {
    state.retryAttempt = 0;
    setConnection("Live", "success");
  });
  socket.addEventListener("message", (message) => {
    try {
      const event = JSON.parse(message.data);
      if (!event || typeof event.event_id !== "string") throw new Error("Malformed Event");
      rememberLiveEvent(event);
    } catch (_error) {
      setConnection("Malformed frame ignored", "warning");
    }
  });
  socket.addEventListener("error", () => setConnection("Connection error", "danger"));
  socket.addEventListener("close", () => {
    if (state.socket === socket) state.socket = null;
    setConnection("Reconnecting", "warning");
    scheduleReconnect();
  });
}

sessionFilter.addEventListener("change", () => selectSession(sessionFilter.value));
channelFilter.addEventListener("change", renderTimeline);
indicatorFilter.addEventListener("change", renderTimeline);
refreshButton.addEventListener("click", () => loadSessions(true));
clearButton.addEventListener("click", () => {
  state.events.clear();
  state.indicators.clear();
  state.selectedEvent = "";
  renderTimeline();
});
window.addEventListener("beforeunload", () => {
  state.stopped = true;
  if (state.reconnectTimer !== null) window.clearTimeout(state.reconnectTimer);
  if (state.socket) state.socket.close();
});

loadSessions();
window.setInterval(() => loadSessions(), 5000);
connect();
