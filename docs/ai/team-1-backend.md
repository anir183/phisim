# Team 1 --- Backend / Platform

## Owned paths

``` text
src/phisim/main.py
src/phisim/telemetry/
src/phisim/infra/
src/phisim/utils/
tests/telemetry/
tests/platform/
tests/test_repository.py
```

## Mission

Provide stable application contracts for scenarios, sessions, events,
persistence, and configuration.

## Phase 0

-   [ ] stabilize event request/response contract
-   [ ] remove stale timestamp input from event tests
-   [ ] add scenario model/repository
-   [ ] add session model/repository
-   [ ] define session lifecycle
-   [ ] expose scenario/session APIs
-   [ ] add event listing by session
-   [ ] document contract changes in `integration.md`

## Phase 1

-   [ ] integrate scenario/session/event relationships
-   [ ] robust duplicate-event handling
-   [ ] add focused integration fixtures
-   [ ] keep WebSocket behavior stable

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

## Avoid

-   editing simulation templates
-   editing console templates
-   embedding analysis rules in repositories
-   large refactors of unrelated backend code
