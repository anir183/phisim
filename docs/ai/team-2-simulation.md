# Team 2 --- Simulation Channels

## Owned paths

``` text
src/phisim/simulation/
scenarios/
web/templates/simulation/
web/static/simulation/
tests/simulation/
```

## Mission

Build safe, fictional phishing experiences on top of the shared
telemetry/session contracts.

## Status

All team-scope P0 and P1 work is complete and integrated on the staging
branch. Every channel funnels through the shared local session cookie
(`phisim_session`) and the same `emit.py` boundary, so all interactions
land in the analyst console's event stream. The staging integration also
registers catalog artifacts as shared Scenarios and persists/reuses the
corresponding Session.

## P0

### Fake credential site

-   [x] scenario metadata
-   [x] fake login page
-   [x] safe submission handling
-   [x] `credential_submission_attempted`
-   [x] educational outcome page
-   [x] test that submitted password is not persisted/emitted

Scenario `credential-basic-001` lives in `phisim/simulation/catalog.py`,
`routes.py`, and `web/templates/simulation/`.

### Email

-   [x] simulated message representation (`EmailMessage` in catalog)
-   [x] message-open interaction (`message_opened`)
-   [x] link-click interaction (`link_clicked`, local redirect)
-   [x] optional harmless attachment interaction (`attachment_opened`)
-   [x] tests

A local fake mailbox is served at `GET /inbox` and `GET /inbox/{id}`.
The message link redirects to
`/scenario/credential-basic-001` (local funnel). No mail provider.

### SMS

-   [x] simulated conversation/message (`SmsThread` in catalog)
-   [x] message-open interaction (`message_opened`)
-   [x] link-click interaction (`link_clicked`, local redirect)
-   [x] tests

A local fake messaging view is served at `GET /sms` and
`GET /sms/{id}`. No SMS provider; fictional sender identities only.

## P1

All ten planned scenario types are implemented as data plus the shared
viewers/routes; no new per-scenario machinery was introduced.

-   [x] spear phishing (`spear-phish-001`)
-   [x] whaling (`whaling-001`)
-   [x] clone phishing (`clone-phish-001`)
-   [x] urgency (`urgency-001`)
-   [x] tech support (`tech-support-001`)
-   [x] QR/quishing (`qr-phish-001`, local QR data URI via existing
    `qrcode[pil]` dependency)
-   [x] attachment (`attachment-phish-001`, inert text representation,
    no payload)
-   [x] link spoofing (`link-spoof-001`, visible label differs from the
    local destination)
-   [x] BEC (`bec-001`)
-   [x] MFA fatigue (`mfa-fatigue-001`, sequential approve/deny prompts
    emitting `mfa_prompt_displayed` / `mfa_prompt_responded`)

Signal-spoofing email variants (`spear-phish-001`, `whaling-001`,
`bec-001`, `clone-phish-001`) reuse the real (fictional) org domain
`techno-main.edu` in the sender address while the actual page serving
host is the phishing domain, demonstrating the mismatch.

## Channels / routes

``` text
GET  /simulation                     lab index (all channels)
GET  /scenario/{id}          POST    fake website (channel=website)
GET  /inbox                  GET /inbox/{id}          GET /inbox/{id}/link
GET  /inbox/{id}/attachment
GET  /sms                    GET /sms/{id}            GET /sms/{id}/link
GET  /qr/{id}                GET /qr/{id}/scan
GET  /mfa/{id}/{step}        POST /mfa/{id}/{step}
```

## Event types emitted (source = browser via `emit.py`)

``` text
scenario_opened
credential_submission_attempted
message_opened            (email and sms)
link_clicked              (email, sms, qr; metadata.target_url is local)
attachment_opened
qr_viewed
mfa_prompt_displayed      (metadata: step, total_steps)
mfa_prompt_responded      (metadata: step, action)
```

Every event carries a `channel` field in metadata and uses the artifact
id as `scenario_id`. Non-credential simulation Events also carry safe
analysis evidence such as `subject`, `content`, `display_host`, link
comparison fields, attachment names, and catalog flags. The funnel for
message/QR links ends at the credential site, so following a link emits
`scenario_opened` there as well (verified by tests).

## Shared indicator glossary

`INDICATOR_INFO` in `catalog.py` documents every indicator code used
across artifacts, including the P1-specific ones
(`personalization`, `spoiled_links`, `invoice_fraud`,
`attachment_lure`, `mfa_fatigue`, `incident_fear`, `tech_support`,
`out_of_band`). Outcome pages render these descriptions.

## Contract expectations

Emit telemetry through the public telemetry boundary.

Do not:

-   import SQLAlchemy models directly (simulation writes go through
    `TelemetryService`)
-   write to SQLite directly
-   modify the analyst console
-   store passwords
-   send real email/SMS
-   use external/real-world domains or organizations

## Design goal

Scenario-specific content is data-driven in `catalog.py` and rendered
by shared templates. No framework was built for each scenario, and no
scenario-authoring format was introduced. For the same reason the
`scenarios/` directory intentionally holds no scenario files yet; the
typed Python registries are the single source of truth until a shared
Team 1 scenario registry exists.

## Security invariants

-   every redirect/encoded QR URL resolves to a local path
-   attachments are inert text only (no executable/file payloads)
-   QR codes are generated in-memory as a data URI (no filesystem
    writes, no static mount required)
-   credentials are only ever checked for presence (field_presence)
-   no external delivery, no persistence of secrets (covered by tests)

## Dependency rule

Satisfied: no third-party dependency was added beyond the project's
existing `qrcode[pil]` for the QR scenario. No SMTP/Twilio/Vonage/SNS/
mail providers are involved.