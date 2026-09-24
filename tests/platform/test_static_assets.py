from fastapi.testclient import TestClient


def test_shared_static_assets_are_local_and_mounted(
    client: TestClient,
) -> None:
    css = client.get("/static/phisim.css")
    console_script = client.get("/static/console.js")
    simulation_script = client.get("/static/simulation.js")

    assert css.status_code == 200
    assert console_script.status_code == 200
    assert simulation_script.status_code == 200
    assert "https://" not in css.text
    assert "http://" not in css.text
    assert "innerHTML" not in console_script.text
    assert "textContent" in console_script.text
    assert "data-transition-ms" in simulation_script.text
    assert ".step-label" in css.text
    assert ".step-dot" in css.text
