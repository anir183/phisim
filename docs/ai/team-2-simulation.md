# Team 2 — Simulation Channels

## Owned paths

```text
src/phisim/simulation/
scenarios/catalog.json
web/templates/simulation/
web/static/phisim.css
web/static/simulation.js
tests/simulation/
```

## Mission

Build safe, convincing fictional security-awareness experiences on top of the
shared Event, Session, analysis, and WebSocket contracts.

## Current status

The simulation layer is integrated with the operator Scenario Lab and the
analyst console. Static scenario content is loaded from the typed local JSON
catalog at `scenarios/catalog.json`. Channel route ownership is split into
focused modules under `src/phisim/simulation/channels/`; the former monolithic
route module is now only a composition router.

All destinations are local. No message is delivered, no external provider is
contacted, and submitted credential values are discarded immediately.

## Information architecture

- `/lab` — operator/scenario control and safe target presets.
- `/simulation` — trainee-facing simulation library.
- `/inbox` and `/inbox/{id}` — fictional Gemail workspace.
- `/sms` and `/sms/{id}` — fictional QuickChat workspace.
- `/scenario/{id}` — two-step parody website login.
- `/qr/{id}` — contextual QR message and local destination preview.
- `/mfa/{id}/{step}` — bounded MFA practice sequence.

## Scenario catalog

The catalog contains:

- UniSecure / Northstar University account verification.
- Amazaun delivery-address and fictional payment-method verification.
- CloudBox storage verification.
- PayMate payment confirmation.
- UniSecure Support security verification.
- Nine Gemail scenarios covering credential phishing, spear phishing,
  whaling, clone phishing, urgency, pretexting, BEC, link spoofing, and
  attachment phishing.
- QuickChat parcel and support scenarios.
- Local QR/quishing and NimbusID MFA-fatigue scenarios.

Catalog records include attack type, channel, fictional brand, target role,
workflow, safe indicators, and local target scenario IDs. Loader validation
rejects duplicate IDs, unknown targets, and non-reserved hosts.

## Channel workflows

### Website

1. Participant opens a parody service shell.
2. Participant submits a fictional username.
3. Participant reaches a separate password step.
4. PhiSim records only boolean `field_presence` facts.
5. Participant reaches a product-specific destination.
6. Participant explicitly ends the simulation to receive the educational reveal.

Credential values are never placed in Event metadata, Session state, response
text, or the database.

### Email

Gemail provides folders, sender/recipient headers, timestamps, previews,
unread/read state, message detail, safe link workflow, and an inert attachment
preview. Link targets are local and catalog-driven.

### SMS

QuickChat provides conversation navigation, sender identity, timestamps,
unread state, message history, a local link, and deterministic typing metadata.
No phone number or SMS provider is contacted.

### QR and attachments

QR content is generated in memory and encodes a local scan route. The scan
action emits `qr_scan_simulated` and redirects to the catalog-selected local
website scenario. Attachments are displayed as metadata and harmless preview
text only; no file is generated, downloaded, or executed.

### MFA

NimbusID presents a bounded sequence of three simulated approval prompts.
Approve/deny transitions, step state, and terminal outcomes are persisted as
safe run state. `instant`, `short`, and `standard` timing profiles are
available; client transitions are bounded and deterministic.

## Telemetry

Meaningful Event types are:

```text
scenario_started              operator launch
scenario_opened               website opened
destination_reached           product destination reached
attack_completed              participant explicitly ended the run
scenario_completed            terminal training outcome
message_opened                email/SMS opened
link_clicked                  email/SMS local link
attachment_opened             inert attachment preview
qr_viewed                     QR message viewed
qr_scan_simulated             local QR scan action
credential_submission_attempted
mfa_prompt_displayed
mfa_prompt_responded
```

Events pass through `phisim.simulation.emit` and the shared telemetry service.
Non-secret catalog evidence includes channel, attack type, local target,
workflow facts, and indicator flags.

## State and architecture

- `catalog.py` contains typed dataclasses and a cached JSON loader.
- `lifecycle.py` owns Session cookie/creation/reuse/completion.
- `state.py` owns a small allowlisted `SimulationRun` state service.
- `channels/` owns website, email, SMS, QR, MFA, and index routes.
- `control.py` owns operator launch/filter behavior.
- `timing.py` owns bounded transition profiles.
- `evidence.py` maps catalog facts to safe analysis evidence.
- `emit.py` remains the telemetry boundary.

`SimulationRun` contains only server-managed state such as read-message IDs,
auth stage, MFA step, and safe action labels. It does not contain credential
values.

## Security invariants

- Every redirect and QR destination is a local path.
- Catalog identities and hosts use fictional parody brands and reserved
  `.example`/`.test`/`.invalid` domains.
- No SMTP, Twilio, Vonage, SNS, browser telemetry, or external assets.
- No shell/process execution, file download endpoint, or executable payload.
- Credential metadata is fail-closed and boolean-only.
- Jinja autoescaping and DOM text APIs remain in use.
- `StaticFiles` serves only the repository's local `web/static/` directory.

## Tests and manual verification

Simulation tests cover route existence, local redirects, Event ordering,
credential non-persistence, read/unread state, distinct parody sites, inert
attachments, QR destinations, MFA transitions, catalog constraints, and static
assets. The full route matrix is covered by
`tests/simulation/test_ui_realism_flows.py`.
