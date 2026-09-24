import asyncio
from typing import cast
from unittest.mock import AsyncMock

from fastapi import WebSocket
from fastapi.testclient import TestClient

from phisim.telemetry.websocket import EventConnectionManager


def test_event_is_broadcast_to_websocket(
    client: TestClient,
) -> None:
    event = {
        "event_id": "event-websocket-001",
        "session_id": "session-001",
        "scenario_id": "credential-basic-001",
        "event_type": "page_viewed",
        "source": "browser",
        "metadata": {
            "page": "/scenario/credential-basic-001",
        },
    }

    with client.websocket_connect("/api/events/ws") as websocket:
        response = client.post(
            "/api/events",
            json=event,
        )

        assert response.status_code == 201

        received = websocket.receive_json()

    assert received["event_id"] == event["event_id"]
    assert received["session_id"] == event["session_id"]
    assert received["scenario_id"] == event["scenario_id"]
    assert received["event_type"] == event["event_type"]
    assert received["source"] == event["source"]
    assert received["metadata"] == event["metadata"]
    assert received["id"] > 0
    assert received["timestamp"].endswith("Z")


def test_event_is_broadcast_to_all_websocket_clients(
    client: TestClient,
) -> None:
    event = {
        "event_id": "event-websocket-002",
        "session_id": "session-002",
        "scenario_id": "credential-basic-001",
        "event_type": "link_clicked",
        "source": "browser",
        "metadata": {
            "url": "/scenario/credential-basic-001",
        },
    }

    with (
        client.websocket_connect("/api/events/ws") as websocket_one,
        client.websocket_connect("/api/events/ws") as websocket_two,
    ):
        response = client.post(
            "/api/events",
            json=event,
        )

        assert response.status_code == 201

        received_one = websocket_one.receive_json()
        received_two = websocket_two.receive_json()

    assert received_one == received_two
    assert received_one["event_id"] == event["event_id"]


def test_unsafe_event_metadata_is_not_broadcast(client: TestClient) -> None:
    with client.websocket_connect("/api/events/ws") as websocket:
        unsafe_response = client.post(
            "/api/events",
            json={
                "event_id": "event-unsafe-websocket",
                "session_id": "session-001",
                "scenario_id": "credential-basic-001",
                "event_type": "credential_submission_attempted",
                "source": "browser",
                "metadata": {"note": "simulated-secret-value"},
            },
        )
        safe_response = client.post(
            "/api/events",
            json={
                "event_id": "event-safe-websocket",
                "session_id": "session-001",
                "scenario_id": "credential-basic-001",
                "event_type": "credential_submission_attempted",
                "source": "browser",
                "metadata": {"field_presence": {"password": True}},
            },
        )
        received = websocket.receive_json()

    assert unsafe_response.status_code == 422
    assert safe_response.status_code == 201
    assert received["event_id"] == "event-safe-websocket"


def test_broadcast_removes_failed_client_and_continues() -> None:
    connection_manager = EventConnectionManager()
    failed_mock = AsyncMock()
    failed_mock.send_json.side_effect = RuntimeError("client disconnected")
    healthy_mock = AsyncMock()
    failed_websocket = cast(WebSocket, failed_mock)
    healthy_websocket = cast(WebSocket, healthy_mock)
    connection_manager.connections.extend([failed_websocket, healthy_websocket])
    event = {"event_id": "event-001"}

    asyncio.run(connection_manager.broadcast(event))

    assert len(connection_manager.connections) == 1
    assert connection_manager.connections[0] is healthy_websocket
    healthy_mock.send_json.assert_awaited_once_with(event)
