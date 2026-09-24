# Team 2 — Final Handover Note

State of the Team 2 simulation work on `feature/team-2`, for the
integrators / merging team.

## What is implemented

All team-scope P0 and P1 simulation channels are complete, integrated,
and tested:

-   Fake credential website (`credential-basic-001`)
-   Fake email mailbox (local, no mail provider) — `GET /inbox`,
    `GET /inbox/{id}`, `GET /inbox/{id}/link`, and an inert
    attachment interaction `GET /inbox/{id}/attachment`
-   Fake SMS messaging (local, conversational) — `GET /sms`,
    `GET /sms/{id}`, `GET /sms/{id}/link`
-   QR quishing — `GET /qr/{id}` renders a local QR PNG data URI that
    encodes `GET /qr/{id}/scan`; both funnel to the credential site
-   MFA fatigue — `GET/POST /mfa/{id}/{step}` sequential
    approve/deny prompts with an educational outcome page
-   Lab index `GET /simulation` cataloguing every channel

The router is registered in `src/phisim/main.py` (telemetry, console,
simulation). All channels share one session cookie
(`phisim_session`), the `phisim/simulation/emit.py` boundary
(`EventRepository` + `TelemetryService`), and the SQLite/WebSocket
event path.

## Points the merging team must consider

### 1. Session is provisional (Team 1 owns the real lifecycle)

Simulation assigns a browser cookie `phisim_session` (32 hex chars,
httponly, samesite=lax) because there is no session API yet. When the
Team 1 session lifecycle lands, swap the cookie for the real
`session_id` in `phisim/simulation/routes.py` — the emit boundary only
needs a valid `session_id`.

### 2. Scenario registry is provisional (Team 1 owns the shared one)

Artifacts are frozen dataclasses in `phisim/simulation/catalog.py`
(`Scenario`, `EmailMessage`, `SmsThread`, `MfaScenario`) with
`get_*` lookups. The `scenarios/` directory is intentionally empty.
Migrate to the Team 1 shared registry by keeping the same ids
(see below) so emitted events remain consistent.

### 3. Artifact ids are the `scenario_id` in events

`scenario_id` carries the artifact id, including message/thread/QR/MFA
ids, e.g. `email-phish-001`, `sms-parcel-001`, `qr-phish-001`,
`mfa-fatigue-001`. Event consumers must not assume a fixed set of
scenario ids.

### 4. New event types added by this work

``` text
message_opened             metadata: { channel: "email" | "sms" }
link_clicked               metadata: { channel, target_url }  # target_url is always local ("/scenario/...")
attachment_opened          metadata: { channel, attachment_name }
qr_viewed                  metadata: { channel: "qr" }
mfa_prompt_displayed       metadata: { channel: "website", step, total_steps }
mfa_prompt_responded       metadata: { channel: "website", step, action }
```

All events include a `channel` metadata field. Following a message/QR
link also emits `scenario_opened` at the credential site (the funnel),
so link interactions produce three events for one session:
`message_opened`/`qr_viewed` → `link_clicked` → `scenario_opened`.

### 5. Indicator glossary is centralized

`INDICATOR_INFO` in `catalog.py` documents every indicator code used,
including the P1 ones (`personalization`, `spoiled_links`,
`invoice_fraud`, `attachment_lure`, `mfa_fatigue`, `incident_fear`,
`tech_support`, `out_of_band`). Analysis/console layers may reuse it
rather than re-derive descriptions.

### 6. Templates use inline CSS

`web/static` is not mounted, so `web/templates/simulation/*` carry
inline styles. Moving to `web/static/simulation/` is a follow-up once
static serving exists; keep the same template file names.

### 7. QR generation dependency

QR codes use the existing `qrcode[pil]` project dependency (no new
dependency was added). Images are generated in-memory as PNG data
URIs — no filesystem writes, so no static mount or temp-dir policy is
needed.

### 8. Test layout

Simulation tests live in `tests/simulation/` and run against the real
`phisim.main.app` via the root `tests/conftest.py` fixtures (`client`,
`test_engine`). There is deliberately no `tests/simulation/conftest.py`
anymore (deleted to avoid a second app fixture).

### 9. Security invariants already enforced by tests

-   Credentials are only checked for presence (boolean
    `field_presence`); the secret is never stored, logged, emitted, or
    broadcast (asserted in `test_site_flow.py`).
-   Every redirect and QR target resolves to a local path.
-   Attachments are inert text only — no payloads, no file execution.
-   All organizations/domains are fictional; nothing is delivered
    externally.

Keep these properties when extending simulation; treat any "real
credential retention" or "external delivery" as a blocking defect.

## Verification

`uv run check` (ruff lint + format check + pyright + full pytest
suite) passes; the full suite is `tests/` with the simulation tests.

## Out of team scope (other teams)

-   Team 1: session lifecycle, shared scenario registry, static
    serving mount.
-   Team 3: analysis/indicators over emitted events.
-   Team 4: console rendering; `web/templates/console.html` still uses
    `innerHTML` for event data and should move to DOM text APIs.

No pushes were made from this branch. Commits are grouped atomically
(feature → tests → docs) and the working tree is clean.

## Integration resolution on `feature/team-1`

The provisional lifecycle concerns above were resolved during staging:

- `phisim_session` now identifies a persisted Team 1 Session created through
  `SessionService`; it is reused across a cross-channel flow.
- Every catalog artifact used by a route is registered through
  `ScenarioService` using its existing stable artifact ID.
- Website credential metadata allows only the typed interaction fields and
  boolean `field_presence`; raw values remain rejected without echo.
- Email, SMS, QR, and MFA Events carry safe evidence fields for the
  deterministic analysis engine, while links and attachments remain local
  and inert.

The historical wording above is retained to document the original handoff;
the current contract is documented in `docs/ai/integration.md` and the final
integration report.
