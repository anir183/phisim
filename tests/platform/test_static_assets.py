from fastapi.testclient import TestClient


def test_shared_static_assets_are_local_and_mounted(
    client: TestClient,
) -> None:
    css = client.get("/static/phisim.css")
    console_script = client.get("/static/console.js")
    simulation_script = client.get("/static/simulation.js")
    victim_script = client.get("/static/victim.js")
    lab_script = client.get("/static/lab.js")
    lab_dashboard_script = client.get("/static/lab-dashboard.js")
    capture_script = client.get("/static/capture-validation.js")
    flow_script = client.get("/static/flow-transition.js")

    assert css.status_code == 200
    assert console_script.status_code == 200
    assert simulation_script.status_code == 200
    assert victim_script.status_code == 200
    assert lab_script.status_code == 200
    assert lab_dashboard_script.status_code == 200
    assert capture_script.status_code == 200
    assert flow_script.status_code == 200
    assert "https://" not in css.text
    assert "http://" not in css.text
    assert "innerHTML" not in console_script.text
    assert "textContent" in console_script.text
    assert "data-transition-ms" in flow_script.text
    assert "flow-transition-loading" in flow_script.text
    assert "flow-transition-spinner" in flow_script.text
    assert 'setAttribute("aria-busy", "true")' in flow_script.text
    assert "textContent" in victim_script.text
    assert "DOMParser" in victim_script.text
    assert "replaceChildren" in victim_script.text
    assert "window.location.reload" not in victim_script.text
    assert "data-attack-id" in lab_script.text
    assert "payload.events" in lab_script.text
    assert "connectLiveEvents" in lab_script.text
    assert "replaceChildren" in lab_script.text
    assert "innerHTML" not in lab_dashboard_script.text
    assert "setInterval(refresh" in lab_dashboard_script.text
    assert "training-only value" in capture_script.text
    assert ".flow-transition-spinner" in css.text
    assert ".console-body .sandbox-console-record dd" in css.text
    assert ".training-reveal-grid > main" in css.text
    assert "align-items: stretch" in css.text
    assert "https://" not in capture_script.text
    assert 'cache: "no-store"' in lab_dashboard_script.text
    assert "quickchat-thread-list" in victim_script.text
    assert 'cache: "no-store"' in victim_script.text
    assert "previousSelection" in console_script.text
    assert "rememberLiveSession" in console_script.text
    assert "renderEventCapture" in console_script.text
    assert "setInterval(() => loadSessions" in console_script.text
    assert ".step-label" in css.text
    assert ".step-dot" in css.text
