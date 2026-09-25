# PhiSim Rebuild Audit

Status: implementation and quality pass complete; seven atomic commits created; no push performed
Repository: `/home/anir183/workspace/phisim/feature/team-1`
Branch: `feature/team-1`
Audit date: 2026-09-25
Scope: audit, architecture cleanup, UI/UX rebuild, simulation realism,
feature expansion, integration, security review, QA, and final-state audit

## Executive Summary

PhiSim is now a coherent local security-awareness laboratory rather than a
collection of prototype screens. The product has three explicit surfaces:

```text
/lab          operator and scenario control
/simulation   trainee-facing fictional applications
/console      analyst review and timeline
```

The implementation remains deliberately local and safe. It uses fictional
parody brands and reserved domains, stores no credential values, sends no
messages, contacts no providers, executes no files or commands, and exposes no
real-targeting or campaign capability.

The integrated backend contracts remain in place. Free-form Event
`session_id`/`scenario_id`, UTC `Z` serialization, duplicate-write behavior,
and fail-closed credential metadata validation were preserved. New work adds
meaningful lifecycle and QR-scan Events, local run state, a typed JSON-backed
catalog, channel-focused route modules, static UI assets, and manual-testing
contracts.

## Current Architecture

### Application entry points

- `src/phisim/main.py` — FastAPI composition root and local static mount.
- `src/phisim/scenarios/` — Scenario CRUD/service/schemas.
- `src/phisim/sessions/` — Session lifecycle service/routes/schemas.
- `src/phisim/telemetry/` — Event validation, persistence, and WebSocket
  broadcast.
- `src/phisim/analysis/` — deterministic indicator rules and Session analysis.
- `src/phisim/inspection/` — UTC-normalized timeline and explanations.
- `src/phisim/security/` — fail-closed Event metadata guardrails.
- `src/phisim/console/` — analyst HTTP integration.
- `src/phisim/infra/sqlite/` — explicit SQLAlchemy models/repositories.
- `web/` — shared shell, fake applications, analyst console, CSS, and JS.
- `scenarios/catalog.json` — local typed scenario content source.
- `tests/` — platform, simulation, analysis, inspection, security, and console
  behavior tests.

### Simulation module ownership

`src/phisim/simulation/routes.py` is now a small composition router. The
previous 626-line multi-channel route module was split into:

```text
src/phisim/simulation/
├── catalog.py       typed catalog loader and lookups
├── channels/
│   ├── common.py    shared template, state, Event, redirect helpers
│   ├── index.py     trainee simulation library
│   ├── website.py   parody site and two-step credential workflow
│   ├── email.py     Gemail list/detail/link/attachment workflow
│   ├── sms.py       QuickChat list/thread/link workflow
│   ├── qr.py        QR context, data URI, simulated scan
│   └── mfa.py       bounded MFA prompt sequence
├── control.py       operator filters and launch behavior
├── lifecycle.py     cookie-backed Scenario/Session lifecycle
├── state.py         allowlisted SimulationRun state service
├── timing.py        bounded deterministic timing profiles
├── evidence.py      safe catalog-to-Event evidence mapping
└── emit.py          shared telemetry boundary
```

### Persistence

The existing tables remain:

- `scenarios`
- `sessions`
- `events`

A fourth table, `simulation_runs`, stores only bounded server-managed workflow
state such as read-message IDs, auth stage, MFA step, and safe action labels.
It has a uniqueness constraint on Session plus Scenario for fresh SQLite
schemas. No credential values, raw message bodies, or arbitrary user state are
stored there.

## Feature Matrix

| Feature                     | Final state                   | Evidence                                               | Notes                                                       |
| --------------------------- | ----------------------------- | ------------------------------------------------------ | ----------------------------------------------------------- |
| Operator Scenario Lab       | Implemented                   | `/lab`, `/api/lab/scenarios`, `/api/lab/launch`        | Filters, safe target presets, timing, recent local runs     |
| Credential phishing         | Implemented                   | `/scenario/{id}`                                       | Two-step username/password flow across five parody services |
| Spear phishing              | Implemented                   | Gemail catalog and `/inbox/{id}`                       | Personalized student scholarship context                    |
| Whaling                     | Implemented                   | Gemail catalog and PayMate target                      | Executive finance/payment context                           |
| Clone phishing              | Implemented                   | Gemail thread-style subject/body                       | Expired shared-file context and out-of-band indicator       |
| Urgency phishing            | Implemented                   | Gemail urgency record                                  | Deadline/lock pressure without a live countdown             |
| Tech-support phishing       | Implemented                   | Gemail + UniSecure Support                             | Dedicated support shell and safe target                     |
| QR phishing                 | Implemented                   | `/qr/{id}` and `/qr/{id}/scan`                         | Local data URI, context, preview, `qr_scan_simulated`       |
| Smishing                    | Implemented                   | `/sms` and `/sms/{id}`                                 | QuickChat shell, unread state, timestamps, typing metadata  |
| Attachment phishing         | Implemented                   | `/inbox/{id}/attachment/preview`                       | Inert metadata/preview only; no file endpoint or payload    |
| Link spoofing               | Implemented                   | Link-spoof Gemail record and local link evidence       | Visible identity and actual local target are both shown     |
| BEC                         | Implemented                   | Apex Office Supplies / PayMate flow                    | Fictional invoice and finance context                       |
| MFA fatigue                 | Implemented                   | `/mfa/{id}/{step}`                                     | Three deterministic prompts, approve/deny, terminal outcome |
| Gemail experience           | Implemented                   | Folders, search, read/unread state, detail, timestamps | Modern local shell                                          |
| QuickChat experience        | Implemented                   | Conversation navigation and message history            | Modern local shell                                          |
| Website variants            | Implemented                   | UniSecure, Amazaun, CloudBox, PayMate, Support         | Distinct brands and local targets                           |
| Meaningful lifecycle Events | Implemented                   | `scenario_started`, `scenario_completed`               | Operator and terminal workflow boundaries                   |
| Session tracking            | Implemented                   | Existing lifecycle plus `SimulationRun`                | Reused active Sessions; new Session after completion        |
| Deterministic analysis      | Implemented                   | `/api/analysis/sessions/{id}`                          | Rule registry, catalog flags, explanations                  |
| Timeline                    | Implemented                   | Analysis timeline and console                          | UTC ordering and Event detail                               |
| Analyst console             | Implemented                   | `/console` + `web/static/console.js`                   | Session list, filters, timeline, evidence, reconnect states |
| Shared UI system            | Implemented                   | `web/static/phisim.css`, `shell.html`                  | Local tokens, responsive primitives, safety strip           |
| Static packaging            | Implemented                   | Hatch includes `web` and `scenarios`                   | Wheel import tested outside repository                      |
| Browser visual automation   | Not implemented               | No connected desktop browser                           | Manual HTTP/HTML and API flows were run instead             |
| External delivery/providers | Intentionally not implemented | Safety requirement                                     | No SMTP, SMS, SNS, or external APIs                         |
| Real targeting/campaigns    | Intentionally not implemented | Safety requirement                                     | Only bounded fictional presets exist                        |

## UI/UX Audit

### Operator surface

`/lab` now has clear product navigation, attack/channel filters, fictional
target-role presets, timing selection, launch actions, safety copy, and recent
local runs. The root route redirects to the lab.

### Trainee surface

`/simulation` clearly identifies the trainee workspace and links to:

- Gemail mailbox and message detail.
- QuickChat conversation list and thread.
- Distinct parody website shells.
- QR message context and destination preview.
- MFA practice.

The website workflow no longer presents username and password as one generic
form. The participant moves through a separate username step and password
step. The UI makes the local/fictional boundary visible without breaking the
fictional application illusion.

### Analyst surface

`/console` now presents:

- active/recent Session navigation;
- channel and indicator filters;
- Session-filtered Event timeline;
- selected Event metadata;
- indicator evidence/explanations;
- loading, empty, error, live, reconnect, and offline states;
- WebSocket updates plus REST recovery.

Dynamic values are rendered with `textContent`, `replaceChildren`, and other
DOM APIs. No `innerHTML`, `eval`, or external script/style dependency exists.

The login step indicator was also corrected after visual review: each bubble is
now a separate `.step-item` with its label below it, and connectors are flex
elements rather than text-adjacent spans. This prevents the Account/Password
labels from overlapping at narrow card widths.

### Visual system

`web/static/phisim.css` provides the shared restrained visual language:
system fonts, neutral surfaces, blue action color, compact status badges,
responsive grids, fake-app sidebars, message rows, chat bubbles, auth cards,
and analyst panels. No remote font, image, telemetry, or CDN request is made.

## Simulation and Telemetry Changes

### Catalog

Static content moved from a Python tuple monolith to
`scenarios/catalog.json`, loaded into typed dataclasses by `catalog.py`.
Loader validation rejects:

- missing sections;
- duplicate identifiers;
- unknown link targets;
- non-reserved catalog hosts.

All current presentation identities use parody brands and reserved domains.
No real organization, mailbox, payment, or support domain remains in the
application source or catalog.

### State transitions

The `SimulationRun` state service provides a small explicit state boundary for
read/unread, authentication stage, MFA step, and safe actions. It rejects
unknown fields, unsafe nested metadata, invalid list sizes, invalid booleans,
out-of-range MFA steps, and unknown action labels.

### Event additions

The existing event vocabulary was preserved. The following meaningful events
were added:

- `scenario_started` — operator launch boundary.
- `scenario_completed` — terminal training boundary.
- `qr_scan_simulated` — explicit local QR interaction.

`qr_scan_simulated` replaces the overly broad QR use of `link_clicked`; email
and SMS link clicks remain `link_clicked`.

### Analysis

The analysis rule table is now an explicit `IndicatorRule` registry. Catalog
indicators produce deterministic evidence without scraping HTML or inferring
intent from arbitrary user prose. New tests exercise every catalog family and
verify at least one expected indicator per scenario.

## Security Review

### Confirmed controls

- Credential Event metadata contains only boolean `field_presence` facts.
- Raw password/username values are not persisted, broadcast, logged, or
  rendered in outcomes.
- Credential validation remains fail-closed and generic.
- Redirects and QR destinations are local paths generated from catalog IDs.
- QR images are generated in memory as data URIs.
- Attachments are inert metadata and text previews only.
- No shell, process, file upload/download, executable, or malware endpoint
  exists.
- No external fonts, assets, analytics, SMTP, SMS, or cloud delivery client
  exists.
- Scenario and target IDs are validated against local catalog/registry data.
- Session and run cookies are HttpOnly and SameSite=Lax.
- Jinja autoescaping and safe browser DOM APIs remain enabled.
- Static mounting is limited to the local `web/static/` directory.
- Catalog and UI source searches found no application `techno-main` or live
  external destination strings.

### Manual security checks performed

- Searched Python/JSON/HTML/JS for external URLs, real-looking domains,
  unsafe DOM insertion, process execution, provider clients, and file-serving
  APIs.
- Inspected Event and analysis responses after a manual credential flow.
- Confirmed a submitted password and username were absent from Event JSON,
  analysis JSON, and rendered outcome HTML.
- Confirmed WebSocket delivery of a safe Event.
- Confirmed wheel-installed catalog/template/static paths resolve outside the
  source checkout.

## Code Quality Audit

### Improvements made

- Split the 626-line simulation route monolith into channel-focused modules.
- Kept route handlers thin around explicit lifecycle/state/telemetry helpers.
- Replaced the static catalog monolith with validated JSON plus typed loaders.
- Extracted a small allowlisted state service instead of introducing a
  generic workflow framework.
- Moved console JavaScript and all non-trivial CSS to local static files.
- Added a shared application shell and local static mount.
- Extracted analysis rules into a named registry.
- Added a packaging-aware path resolver for source and wheel layouts.
- Fixed a real JSON response bug where copied `Content-Length: 0` from a
  temporary cookie response caused `/api/lab/launch` to return an empty body.
- Corrected the new operator launch response to preserve its JSON body while
  copying only the safe cookie header.
- Added the missing `university employee` fictional target preset to the
  operator allowlist and added catalog/API/form regression coverage for the
  UniSecure Support launch path.
- Added a root redirect to `/lab`.

### Deliberately retained choices

- FastAPI, Jinja, SQLAlchemy/SQLite, Pydantic, WebSocket, and explicit
  repositories remain the foundation.
- No generic repository framework, CQRS, event sourcing, plugin system, or
  large frontend framework was introduced.
- Existing public Event/Session contracts remain compatible.
- Historical canonical documents were not rewritten as part of this pass;
  `docs/ai/REBUILD_AUDIT.md` and `docs/ai/team-2-simulation.md` reflect the
  rebuilt product.

## Tests and Command Evidence

### Final automated commands

```text
uv run test
143 passed, 1 warning

uv run lint
All checks passed!

uv run format --check .
102 files left unchanged

uv run typecheck
0 errors, 0 warnings, 0 informations

uv run check
passed
```

The remaining warning is the existing Starlette/httpx `TestClient`
deprecation warning. No test was deleted or weakened to hide a product defect.
Existing assertions were updated only where the documented content/workflow
contract intentionally changed (fictional brands, two-step website flow,
explicit QR Event, MFA channel, and terminal lifecycle Event).

Additional checks:

```text
node --check web/static/console.js
passed

node --check web/static/simulation.js
passed

uv build --wheel --out-dir /tmp/opencode/phisim-dist
Successfully built phisim-0.0.0-py3-none-any.whl
```

The built wheel was unpacked outside the repository and imported successfully;
its `scenarios/catalog.json`, `web/templates`, and `web/static` assets were
present and resolved.

### Manual local verification

A local HTTP flow was run against the running `127.0.0.1:8000` development
server with a cookie jar. A separate temporary wheel installation was used for
packaging verification.

```text
/                                         307 -> /lab
/lab                                      200
/api/lab/launch                           200
/api/lab/scenarios?channel=email          200
/inbox/email-phish-001                    200
/scenario/credential-basic-001            200
/scenario/.../username                    303
/scenario/.../password                    200
/scenario/credential-shopping-001         200
/console                                  200
/static/console.js                        200
```

The resulting Event sequence was:

```text
scenario_started
message_opened
scenario_opened
credential_submission_attempted
scenario_completed
```

Analysis contained four indicators, and the manually supplied fictional
username/password were absent from Event and analysis JSON.

A Python WebSocket smoke check connected to `/api/events/ws`, submitted one
safe Event, and received the matching Event ID and type.

## MCP Usage

### Context7

Context7 was consulted for current documentation on:

- FastAPI `StaticFiles` and lifespan initialization;
- Jinja autoescaping;
- SQLAlchemy request-scoped Session lifecycle patterns.

### Yaak

Workspace and environment:

- workspace: `PhiSim` / `wk_dvBfLUkGqf`;
- environment: `Development` / `ev_KcsyLERshT`.

A permanent local folder was created for the rebuilt smoke suite:

- folder: `PhiSim Rebuild` / `fl_yeDVyHEMhf`.

Updated/created HTTP requests include:

- `Create Event` / `rq_iAvxCqrE3g` — safe Event contract, status 201.
- `Simulation Index` / `rq_HkxFtcRq7z` — status 200.
- `Lab Scenario Catalog` / `rq_HhtrXbsF7k` — status 200.
- `Launch Fictional Scenario` / `rq_JCpzNmi8ec` — status 200 with a valid
  Session/run JSON body.
- `List Sessions` / `rq_qpTCAoywSe` — status 200.
- `Session Events` / `rq_bz44E5uwuZ` — status 200 using a chained launch
  response.
- `Session Analysis` / `rq_utzwKqdmQS` — status 200 using a chained launch
  response.
- `Fictional Website` / `rq_waXX5YBavv` — status 200.
- `QR Destination Preview` / `rq_JSDHkh2E6m` — status 200.

The existing WebSocket request remains:

- `Event WebSocket` / `wr_dqi5dAnBC4`.

Two integration defects were found and corrected during Yaak smoke testing:
an initial `/api/simulation` URL was corrected to `/simulation`, and the
launch endpoint's empty-body `Content-Length` header was fixed. All listed
requests were rerun successfully afterward. The WebSocket was independently
verified locally because the available MCP catalog did not expose a WebSocket
send/update operation.

## Implementation Passes

- [x] Baseline audit and persistent audit artifact.
- [x] Architecture/code-quality pass and channel route split.
- [x] Information architecture and shared UI pass.
- [x] Scenario catalog and fictional identity pass.
- [x] Website, email, SMS, QR, attachment, and MFA realism pass.
- [x] Telemetry, state, analysis, console, and WebSocket integration pass.
- [x] Security review and local constraint tests.
- [x] Yaak request/folder update and local request smoke tests.
- [x] Full automated QA and wheel packaging check.
- [x] Final audit and known-limitation classification.

## Final State

### Implemented

- Three-surface information architecture: Lab, Simulations, Analyst Console.
- Validated local JSON scenario catalog with parody brands and reserved
  domains.
- Two-step credential workflow with boolean-only telemetry.
- Gemail, QuickChat, QR, attachment preview, MFA, and five parody service
  shells.
- Local run state for meaningful read/auth/MFA transitions.
- Meaningful launch/completion/QR Events.
- Deterministic analysis registry and expanded catalog evidence.
- Modern local CSS/JS system with safe DOM rendering and static mounting.
- Scenario Lab filters, launch controls, timing profiles, and recent runs.
- Console filters, timeline/detail/evidence views, reconnect/error states.
- Local-only API/manual/Yaak/WebSocket verification.
- Wheel packaging for source assets and catalog.

### Partially Implemented

- Browser visual regression and screenshot coverage: the desktop browser was
  not connected in this session, so verification used HTML/API/manual flows.
- Rich mailbox folders and production-grade search: search and folders are
  present as local UX primitives, but are not a full mail backend.
- Timing realism: bounded client transitions and timing profiles exist; there
  are no artificial server sleeps.
- Legacy SQLite schema evolution: fresh databases receive the new run table;
  the project still relies on `create_all` rather than a migration framework.

### Not Implemented

- Real credential collection, persistence, replay, or transmission.
- SMTP, SMS, SNS, email, or cloud-provider integrations.
- Real people, real brands, real domains, public campaigns, or real targeting.
- Malware, executable attachments, shell/process execution, stealth, or
  persistence.
- External telemetry, remote fonts, remote images, or CDN assets.
- Automated browser visual regression, because no desktop browser connection
  was available.

These omissions are intentional safety/product decisions, not unfinished core
features.

### Removed

- The 626-line multi-channel route monolith.
- Inline console JavaScript and non-trivial inline CSS.
- Real-looking `techno-main` content from the application source/catalog.
- Python-tuple-only scenario content as the source of truth.
- The overly broad QR `link_clicked` interpretation in favor of the explicit
  `qr_scan_simulated` event.

No team work, tests, or useful namespace re-exports were deleted.

### Architecture Changes

See the module ownership and persistence sections above. The implementation
uses explicit repositories/services and no generic framework.

### UI Changes

See the UI/UX audit above. All three surfaces share local tokens and safety
language while fake applications remain visually distinct from the analyst
console.

### Simulation Changes

See the feature matrix and simulation/telemetry sections above.

### Test Results

Final results are recorded in the Tests and Command Evidence section. The
suite currently has 143 passing tests with one pre-existing deprecation
warning.

### Manual Verification

Local HTTP, Event persistence, analysis, WebSocket, static assets, and wheel
import checks are recorded above. Desktop-browser visual verification remains
unavailable in this session and is explicitly classified as a limitation.

### MCP Usage

Context7 and Yaak usage, IDs, request statuses, and the two corrected smoke-
test defects are recorded in the MCP Usage section.

### Remaining Work by Priority

#### P0

None identified.

#### P1

None required for the local product scope.

#### P2

- Add a connected-browser visual/accessibility pass when a desktop browser is
  available.
- Add a lightweight screenshot or DOM smoke harness if the team wants
  continuous visual regression.
- Add an explicit migration strategy if deployed SQLite databases must evolve
  beyond `create_all`.

#### P3

- Expand mailbox folders and search semantics if a fuller mail-lab workflow
  is desired.
- Add richer analyst filtering/export features after core usage is validated.

### Known Limitations

- No desktop browser connection was available, so no screenshot or browser
  interaction evidence could be recorded.
- The local server uses the existing SQLite `create_all` initialization model.
- The static catalog is intentionally small and data-driven rather than a
  general scenario scripting engine.
- Client-side timing transitions are deterministic but do not emulate complex
  network latency.
- The analyst console is intentionally local and single-process; it does not
  provide multi-user authentication or distributed storage.
- Historical canonical documents may describe the pre-rebuild prototype; the
  current implementation record is this audit plus the updated Team 2 AI
  document.

## Git and Handoff State

The implementation, tests, audit, and local Yaak work are recorded in seven
atomic local commits on `feature/team-1`. `.opencode/` and `opencode.json`
remain untracked and unstaged. No push, history rewrite, or unrelated
team-work deletion was performed.
