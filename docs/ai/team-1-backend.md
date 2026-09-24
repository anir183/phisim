# Team 1 --- Backend / Platform

## Owned paths

``` text
src/phisim/main.py
src/phisim/telemetry/
src/phisim/infra/
src/phisim/scenarios/
src/phisim/sessions/
src/phisim/utils/
tests/telemetry/
tests/platform/
tests/test_repository.py
```

## Mission

Provide stable application contracts for scenarios, sessions, events,
persistence, and configuration.

## Phase 0

-   [x] stabilize event request/response contract
-   [x] remove stale timestamp input from event tests
-   [x] add scenario model/repository
-   [x] add session model/repository
-   [x] define session lifecycle
-   [x] expose scenario/session APIs
-   [x] add event listing by session
-   [x] enforce credential-safe event metadata
-   [x] document contract changes in `integration.md`

## Phase 1

-   [x] finalize the Event/Session relationship as free-form Event
  identifiers with Session-filtered retrieval for P0 compatibility
-   [x] robust duplicate-event handling under concurrent writes
-   [x] add focused integration fixtures
-   [x] keep WebSocket behavior stable

## Contract supplied to other teams

### Simulation -\> telemetry

Simulation should be able to submit an event equivalent to:

``` text
event_id
session_id
scenario_id
event_type
source
metadata
```

Timestamp remains server-generated.

### Console -\> backend

The console should consume HTTP/API responses and WebSocket events.

It must not access SQLAlchemy models.

### Analysis -\> backend

Analysis consumes safe event/session data.

No password value is ever part of the contract.

## Implemented HTTP contracts

### Scenario

- `POST /api/scenarios`
- `GET /api/scenarios`
- `GET /api/scenarios/{scenario_id}`

Scenario IDs are caller-supplied stable identifiers. Creation timestamps
are server-generated. Duplicate IDs return `409`; missing scenarios return
`404`.

### Session

- `POST /api/sessions`
- `GET /api/sessions`
- `GET /api/sessions/{session_id}`
- `POST /api/sessions/{session_id}/complete`

A Session requires an existing Scenario. `session_id` is optional in the
create request and generated when omitted. Status is server-managed and is
limited to `active` and `completed`. Completion is idempotent.

### Event retrieval and safety

- `GET /api/events?session_id=...` returns persisted events in timestamp
  order.
- Event `session_id` and `scenario_id` remain free-form strings for
  backward compatibility; Event creation does not require persisted rows.
- Duplicate Scenario, Session, and Event identifiers return `409`.
  Repository conflicts roll back before services verify and translate the
  collision; unrelated integrity errors are not hidden.
- All non-null Scenario, Session, and Event timestamps use ISO 8601 UTC
  with a trailing `Z` in HTTP and WebSocket contracts.
- `EventCreate` rejects unknown fields, including a client-supplied
  `timestamp`.
- `credential_submission_attempted` accepts only a `field_presence`
  dictionary whose values are booleans. Other metadata is rejected before
  persistence and broadcast.
- Request validation failures return a generic `422` response without
  echoing submitted input.

## Verification status

Focused backend tests cover Scenario/Session APIs, repositories, Event
retrieval, sequential and simulated unique-write races, UTC timestamp
serialization, application lifespan initialization, credential metadata
allowlisting, validation-error redaction, and WebSocket delivery after a
client failure. Full project checks are recorded in the implementation
handoff.

## Avoid

-   editing simulation templates
-   editing console templates
-   embedding analysis rules in repositories
-   large refactors of unrelated backend code
