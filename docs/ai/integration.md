# Cross-Team Integration

## Current dependency graph

``` text
Team 1 backend/platform
       |
       +----> Team 2 simulation
       |
       +----> Team 3 analysis
       |
       +----> Team 4 console

Team 2 simulation
       |
       v
Team 1 telemetry
       |
       v
Team 3 analysis
       |
       v
Team 4 console
```

This is a dependency graph, not a quality ranking.

## Integration order

1.  backend/event contracts
2.  scenario/session contracts
3.  fake-site vertical slice
4.  analysis integration
5.  console integration
6.  email
7.  SMS
8.  remaining scenarios

Email/SMS may be developed in parallel after the basic telemetry
contract is stable.

## Shared contract checklist

Before changing a shared contract:

-   [ ] identify all consumers
-   [ ] write the intended change here
-   [ ] make the smallest compatible change
-   [ ] add/update tests
-   [ ] notify affected team
-   [ ] avoid simultaneous edits to the same root files

## P0 integration scenario

``` text
start session
    |
open fake site
    |
submit fake credentials
    |
emit credential_submission_attempted
    |
persist event
    |
run analysis
    |
broadcast event
    |
console displays event + indicator
```

## Current known cleanup

None open from Team 2. The earlier note about stale `timestamp` input
in event tests was resolved in commit `2f6e132` (timestamp is
server-generated); the simulation integration on `feature/team-2` is
wired into `phisim.main.app` and covered by tests.

## Simulation integration notes (Team 2)

Team 2's P0 (fake website, email, SMS) and all P1 scenario types are
implemented on `feature/team-2` and registered in `src/phisim/main.py`.
Contract notes for Team 1 / integrators:

-   **Session source:** there is no session API yet, so the simulation
    assigns a browser cookie `phisim_session` (random hex token) and
    reuses it across every channel (website, email, SMS, QR, MFA). This
    is provisional until Team 1 exposes a session lifecycle;
    `TelemetryService` currently accepts any `session_id`.
-   **Emit boundary:** `phisim/simulation/emit.py` composes
    `EventRepository` + `TelemetryService` (the same composition the
    telemetry routes use) and records an `EventCreate`. No SQLAlchemy
    writes live in simulation code.
-   **Router registration:** `simulation_router` is included in
    `src/phisim/main.py` alongside the telemetry and console routers.
-   **Artifact identity:** events carry the artifact id as
    `scenario_id` (a scenario id for website/QR/MFA artifacts, a
    message id for email/SMS artifacts): e.g. `email-phish-001`,
    `sms-parcel-001`, `qr-phish-001`, `mfa-fatigue-001`.
-   **Event types:** in addition to `scenario_opened` /
    `credential_submission_attempted`, simulation emits
    `message_opened`, `link_clicked`, `attachment_opened`, `qr_viewed`,
    `mfa_prompt_displayed`, and `mfa_prompt_responded`. Metadata always
    includes a `channel` field; `link_clicked` includes a local
    `target_url`.
-   **Indicator glossary:** `catalog.py`'s `INDICATOR_INFO` documents
    both the original four indicators and the P1 indicator codes so the
    analysis/console layers can render descriptions without importing
    simulation internals.
-   **Templates:** live under `web/templates/simulation/` with inline
    CSS because `web/static` is not mounted yet. Externalizing to
    `web/static/simulation/` is a follow-up once static serving exists.
-   **Scenario metadata:** a local registry in
    `phisim/simulation/catalog.py` (frozen dataclasses) pending the
    Team 1 shared scenario registry.
-   **QR quishing:** QR codes are rendered by the existing
    `qrcode[pil]` dependency as in-memory PNG data URIs encoding the
    local `/qr/{id}/scan` route; no external QR services.

## Integration rule

If an implementation can wait for another team's stable contract, do not
bypass the contract by importing that team's internals.

## First 2--3 hour team run

The first shared session should optimize for a working vertical slice,
not feature count.

### Parallel start

``` text
Team 1: Event + Scenario + Session contracts
Team 2: Fake credential site
Team 3: Indicator fixtures/rules + secret-safety test
Team 4: Console event/session view
```

### Integration checkpoint

At the end of the first run:

``` text
fake site
  -> event
  -> persistence
  -> analysis
  -> WebSocket
  -> console
```

Do not start email/SMS integration until this path works.

### Next run

Use the same primitives to add:

``` text
fake email inbox -> fake email -> local link
fake SMS thread  -> fake message -> local link
```

No external delivery APIs are involved.

## Integration checklist

-   [ ] scenario can be identified without hardcoded UI-only state
-   [ ] session is created/reused correctly
-   [ ] event has stable event_id
-   [ ] timestamp is server-generated
-   [ ] submitted password never appears in event metadata
-   [ ] duplicate events are handled deterministically
-   [ ] analysis consumes events rather than database internals
-   [ ] console consumes API/WebSocket contracts rather than SQLAlchemy
-   [ ] all links remain local
-   [ ] no external delivery provider is configured
