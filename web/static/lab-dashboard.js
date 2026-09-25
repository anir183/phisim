"use strict";

const dashboard = document.querySelector("[data-lab-dashboard]");
if (dashboard) {
  const activePanel = dashboard.querySelector("[data-lab-active-panel]");
  const recentPanel = dashboard.querySelector("[data-lab-recent-panel]");
  const activeCount = document.getElementById("lab-active-count");
  const sessionCount = document.getElementById("lab-session-count");
  let inFlight = false;
  let lastFingerprint = "";

  function text(value) {
    return typeof value === "string" ? value : value == null ? "" : String(value);
  }

  function element(tag, value, className) {
    const node = document.createElement(tag);
    node.textContent = text(value);
    if (className) node.className = className;
    return node;
  }

  function link(value, label, className) {
    const node = document.createElement("a");
    node.href = value;
    node.textContent = text(label);
    if (className) node.className = className;
    return node;
  }

  function tableBody(panel, headers) {
    let body = panel.querySelector("tbody");
    if (body) return body;
    const empty = panel.querySelector(".operator-empty");
    const wrap = document.createElement("div");
    wrap.className = "operator-table-wrap";
    const table = document.createElement("table");
    table.className = "operator-table";
    const head = document.createElement("thead");
    const headRow = document.createElement("tr");
    for (const header of headers) headRow.appendChild(element("th", header));
    head.appendChild(headRow);
    body = document.createElement("tbody");
    table.append(head, body);
    wrap.appendChild(table);
    if (empty) empty.replaceWith(wrap);
    else panel.appendChild(wrap);
    return body;
  }

  function attackRow(attack) {
    const row = document.createElement("tr");
    const identity = document.createElement("td");
    const attackLink = link(`/lab/attacks/${encodeURIComponent(attack.attack_id)}`, text(attack.attack_id).slice(0, 10));
    const code = document.createElement("code");
    code.textContent = text(attack.attack_id).slice(0, 10);
    attackLink.replaceChildren(code);
    identity.append(attackLink, document.createElement("br"), element("span", attack.scenario_id));
    const channel = document.createElement("td");
    channel.appendChild(element("span", attack.channel, "operator-channel"));
    const status = document.createElement("td");
    const phase = text(attack.phase || attack.status);
    status.appendChild(element("span", phase, `badge ${attack.status === "COMPLETED" ? "badge-success" : "badge-warning"}`));
    row.append(identity, channel, status, element("td", attack.delivery_due_at), link(attack.victim_path, "Open context →"));
    return row;
  }

  function sessionRow(session) {
    const row = document.createElement("tr");
    const identity = document.createElement("td");
    const code = document.createElement("code");
    code.textContent = text(session.session_id).slice(0, 12);
    identity.appendChild(code);
    const status = document.createElement("td");
    status.appendChild(element("span", session.status, `badge ${session.status === "completed" ? "badge-success" : "badge-warning"}`));
    row.append(identity, element("td", session.scenario_id), status, element("td", session.started_at));
    return row;
  }

  function render(payload) {
    const attacks = Array.isArray(payload.attacks) ? payload.attacks : [];
    const sessions = Array.isArray(payload.sessions) ? payload.sessions : [];
    if (activePanel) {
      const body = tableBody(activePanel, ["Attack", "Channel", "Status", "Delivery", "Victim context"]);
      body.replaceChildren(...attacks.map(attackRow));
    }
    if (recentPanel) {
      const body = tableBody(recentPanel, ["Session", "Scenario", "Status", "Started"]);
      body.replaceChildren(...sessions.map(sessionRow));
    }
    if (activeCount) activeCount.textContent = String(attacks.length);
    if (sessionCount) sessionCount.textContent = String(sessions.length);
  }

  async function refresh() {
    if (inFlight) return;
    inFlight = true;
    try {
      const response = await fetch(`/api/lab/dashboard?_=${Date.now()}`, {
        cache: "no-store",
        headers: { Accept: "application/json" },
      });
      if (!response.ok) throw new Error("Dashboard request failed");
      const payload = await response.json();
      const fingerprint = JSON.stringify(payload);
      if (fingerprint === lastFingerprint) return;
      lastFingerprint = fingerprint;
      render(payload);
      dashboard.dataset.liveState = "ready";
    } catch (_error) {
      dashboard.dataset.liveState = "retrying";
    } finally {
      inFlight = false;
    }
  }

  void refresh();
  window.setInterval(refresh, 2000);
}
