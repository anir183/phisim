# PhiSim Realism / State / Workflow Audit

Status: implementation complete; final QA and manual HTTP verification recorded below
Repository: `feature/team-1`
Audit date: 2026-09-25
Scope: end-to-end incident realism, operator/victim separation, dynamic delivery,
scenario-specific workflows, timing, and analyst continuity

## Audit Method

The audit read the current canonical documentation and implementation rather than
assuming that documented architecture was already active:

- `docs/README.md`
- `docs/PLAN.md`
- `docs/ARCHITECTURE.md`
- `docs/SECURITY.md`
- `docs/DECISIONS.md`
- `docs/ai/REBUILD_AUDIT.md`
- `/lab`, `/simulation`, `/scenario/*`, `/inbox`, `/sms`, `/qr/*`, `/mfa/*`,
  `/console`, and the `/api/*` route implementations
- Scenario catalog, Session lifecycle, `SimulationRun` state, Event emission,
  analysis, inspection, and WebSocket paths

The existing `REBUILD_AUDIT.md` describes the visual/product reconstruction that
already landed. This audit intentionally evaluates a stricter question: does the
runtime behave like an incident unfolding inside a victim's environment?

## Current Flow

The actual behavior is currently:

```text
Operator opens /lab
        ↓
Operator chooses a catalog scenario
        ↓
POST /api/lab/launch or POST /lab/launch
        ↓
ensure_simulation_session() creates/reuses a browser Session
        ↓
scenario_started is emitted immediately
        ↓
operator is redirected or returned directly to the selected channel
        ↓
victim-facing page renders static catalog content
        ↓
user opens/clicks/interacts
        ↓
action Event is emitted
        ↓
terminal interaction emits scenario_completed
        ↓
training outcome renders
        ↓
console reads Events/timeline through REST and WebSocket
```

The current flow is safe and functional, but it is not yet a true delivery
simulation. The operator and victim are not separate actors, and the victim
environment does not begin in an ordinary state and change after an attack is
launched.

## Current State Ownership

### Sessions

`ensure_simulation_session()` in `simulation/lifecycle.py` owns the
`phisim_session` cookie. It registers catalog artifacts as Scenarios, reuses an
active Session, creates a new Session after completion, and completes terminal
website/MFA flows.

The cookie is shared by tabs in the same browser. Therefore, it cannot by
itself represent an independent operator browser and victim browser.

### Attack/run state

`SimulationRun` in `simulation_runs` stores small JSON state such as:

- read-message IDs;
- read-thread IDs;
- auth stage;
- MFA step;
- safe action labels.

It does not currently represent a complete attack lifecycle, delivery schedule,
independent operator/victim identities, or channel-specific incident state.

### Email

`EMAIL_MESSAGES` is a static catalog loaded from `scenarios/catalog.json`.
`/inbox` renders those records immediately, optionally filtered by `q` and by
read IDs in `SimulationRun` state. There is no baseline/delivered distinction:
future phishing messages are visible before launch.

Opening `/inbox/{message_id}` creates/reuses a Session, marks the message read,
and emits `message_opened`. Clicking the local link emits `link_clicked` and
redirects immediately to the target website.

### SMS

`SMS_THREADS` is also static. `/sms` renders all configured conversations and
uses `read_thread_ids` to change unread state. There is no delivery event,
arrival transition, notification, or conversation instance created at launch.

### Website

All website scenarios use the same broad username → password → completion
shape. Brands, hosts, labels, and indicators differ, but the interaction model
and post-submission behavior remain largely universal. The completion path
immediately renders the training outcome after recording the credential
attempt.

### QR

`/qr/{id}` renders an in-memory QR data URI and local destination preview.
`/qr/{id}/scan` redirects directly to a local website and emits
`qr_scan_simulated`. It is safe and local, but it is not embedded in a delayed
message-delivery lifecycle.

### MFA

`/mfa/{id}/{step}` renders a bounded prompt sequence and records displayed/
responded Events. It has client transition timing, but it is not driven by an
attack delivery state or a shared operator/victim context.

### Events and analysis

Simulation code emits Events through `simulation/emit.py`; TelemetryService
persists, analyzes, and broadcasts them. Analysis is deterministic and
Event-driven. The console uses REST recovery and WebSocket updates.

The current Event sequence is useful, but it begins at `scenario_started` and
then records user actions. It does not yet include a distinct delivery boundary
or a complete attack state timeline.

## Problems

### Lifecycle and delivery

- Attack launch is effectively page navigation.
- No `ARMED`, `DELIVERED`, `ENGAGED`, `ABANDONED`, or `EXPIRED` state exists.
- No delivery event exists.
- No scheduled delivery or deterministic simulation clock exists.
- No independent operator and victim Session/context exists.

### Victim state

- Email and SMS content is visible before launch.
- Inbox and SMS have no ordinary baseline dataset.
- Attack delivery cannot create a new unread message instance.
- Refreshing preserves only limited read state; it does not preserve a complete
  incident context.
- Website, inbox, SMS, and attack state are not modeled as one victim timeline.

### Workflow differentiation

- Too many attacks still reduce to message → link → username/password.
- University, shopping, cloud, payment, and support pages share one structural
  template.
- Processing/result behavior before the training reveal is too short.
- BEC, clone, urgency, and support mechanisms are primarily content differences,
  not distinct interaction models.
- MFA and QR are separate routes, but not part of a common scheduled incident.

### Timing

- There is no 1–3 second message-delivery delay.
- Timing is limited to short form/UI transitions.
- There is no test-mode clock/provider for delivery and processing states.
- The user can move through the entire incident too quickly.

### UI and disclosure

- Victim applications are visually improved but still reveal the simulation
  context too early in some workflows.
- The fake applications need more identity, context, and believable metadata.
- The operator needs active-attack status and a victim link/session reference.
- The console needs the complete incident lifecycle rather than only action
  events after arrival.

## Required Reconstruction

The target experience is:

```text
Operator /lab
        ↓
create/select a safe fictional attack
        ↓
Attack becomes ARMED
        ↓
Scenario Engine schedules deterministic delivery
        ↓
Victim environment receives ordinary baseline content
        ↓
delivery becomes DELIVERED
        ↓
new unread email/SMS/QR context appears
        ↓
victim opens message
        ↓
attack becomes ENGAGED
        ↓
victim follows an attack-specific workflow
        ↓
meaningful Events are recorded
        ↓
scenario-specific processing/result occurs
        ↓
training reveal appears
        ↓
attack/session becomes COMPLETED
        ↓
analyst console displays the complete timeline
```

## Target Architecture

Keep the existing FastAPI/Jinja/SQLAlchemy stack and explicit repositories. Add
only the smallest state needed for a believable local incident.

### Actor separation

Use an explicit local demo context so operator and victim tabs are independent
even when browser cookies are shared. The victim link should carry an opaque,
local-only context token or route identifier. The token must not contain a
credential or a real identity.

Suggested conceptual flow:

```text
operator browser cookie ──> operator Session
victim URL token ────────> victim Session/context
both ────────────────────> AttackRun
```

### Attack lifecycle

Use a small explicit state machine:

```text
DRAFT → ARMED → LAUNCHING → DELIVERED → ENGAGED → COMPLETED
```

Optional terminal states:

```text
ABANDONED
EXPIRED
BLOCKED
```

State transitions must be validated by a service, not inferred from route
names.

### Delivery state

Add a small persisted delivery/message concept for:

- ordinary baseline messages;
- attack email messages;
- attack SMS messages;
- QR/message context;
- website/MFA attack context.

A delivery should have a due time, delivered time, read/open time, and safe
scenario reference. Tests use an injected clock or an `instant` profile.

### Event vocabulary

Preserve existing free-form Event contracts and add only meaningful lifecycle
Events:

```text
attack_armed
message_delivered
message_opened
link_clicked
website_viewed
credential_submission_attempted
attachment_opened
qr_scan_simulated
mfa_prompt_displayed
mfa_prompt_responded
attack_completed
```

The console and analysis must consume these through the existing Event API and
WebSocket boundary.

## Simulation Matrix

| Attack              | Channel                 | Distinct workflow                   | Dynamic delivery           | Events                        | Analysis                                    | Tested                              |
| ------------------- | ----------------------- | ----------------------------------- | -------------------------- | ----------------------------- | ------------------------------------------- | ----------------------------------- |
| Credential phishing | Email/SMS → website     | service-specific authentication     | delayed unread message     | delivery/open/link/submission | credential, urgency, domain, authority      | Existing baseline; rebuild required |
| Spear phishing      | Email                   | personalized academic request       | delayed targeted message   | delivery/open/link/action     | personalization, authority, urgency         | Existing data; rebuild required     |
| Whaling             | Email → payment/support | executive/finance request           | delayed executive message  | delivery/open/action          | authority, invoice, urgency                 | Existing data; rebuild required     |
| Clone phishing      | Email                   | copied thread with changed action   | delayed familiar thread    | delivery/open/link            | personalization, out-of-band, link mismatch | Existing data; rebuild required     |
| Urgency phishing    | Email/web               | deadline/countdown then request     | delayed warning            | delivery/open/action          | urgency, incident fear                      | Existing data; rebuild required     |
| Pretexting          | Web/email               | incident → support verification     | delayed support context    | delivery/open/verification    | authority, support, incident fear           | Existing baseline; rebuild required |
| QR phishing         | Message/poster → QR     | scan and destination preview        | delayed message context    | delivery/view/scan            | domain, urgency, QR                         | Existing baseline; rebuild required |
| Smishing            | SMS                     | conversation plus unexpected link   | delayed unread message     | delivery/open/link            | urgency, impersonation, domain              | Existing baseline; rebuild required |
| Attachment phishing | Email → document        | preview and follow-up               | delayed attachment message | delivery/open/attachment      | attachment lure, credential request         | Existing baseline; rebuild required |
| Link spoofing       | Email                   | visible/actual destination mismatch | delayed familiar request   | delivery/open/link            | link mismatch, domain                       | Existing baseline; rebuild required |
| BEC                 | Email → payment         | executive/finance instruction       | delayed finance request    | delivery/open/action          | authority, invoice, urgency                 | Existing data; rebuild required     |
| MFA fatigue         | Website/device          | repeated prompts and response       | scheduled prompt sequence  | displayed/responded           | MFA fatigue, unusual context                | Existing baseline; rebuild required |

## UI Applications

### Gemail

Fictional mail client with sidebar folders, unread counts, an empty baseline
state, search, rich message headers, signatures, quoted context, safe
attachments, reply/forward affordances, and dynamically delivered attack mail.

### QuickChat

Fictional messenger with contacts, avatars, an empty baseline state, unread
badges, incoming/outgoing bubbles, timestamps, delivery state, link previews,
and dynamically delivered attack SMS.

### Distinct mock-site system

The primary `/v/{token}/...` flow and the legacy `/scenario/...` compatibility
flow now share a local theme registry and CSS token system. Each target has its
own landing/home composition and visual identity: Gemail, QuickChat, UniSecure,
UniSecure Support, Amazaun, CloudBox, PayMate, MAKExam, TechnoSphere, and
NimbusID. QR and MFA surfaces use the corresponding target/device theme.

All marks, layouts, icons, and illustrations are local CSS/text/SVG-style
surfaces. No external assets, fonts, requests, or real service endpoints are
used.

### Landing and completion controls

Website targets open on a branded home/landing page with service-specific
navigation, status cards, and a scenario CTA. The generic processing page is no
longer part of the normal completion path; final actions move directly to the
themed training debrief. Every website landing/verification page includes a
local `End simulation` control that safely completes the interaction without
collecting credentials.

### MAKExam / TechnoSphere

Fictional examination and college portals inspired by familiar academic UX
conventions without copying real MAKAUT pages, brands, assets, or endpoints.
They should use distinct terminology, navigation, content, and workflows.

### UniSecure Support

A support-incident shell with device/context, incident reference, support
identity, verification step, and support-specific outcome.

### Amazaun / CloudBox / PayMate

Separate service identities with different navigation, terminology, form
structure, workflow states, and outcomes. They must not reuse one universal
login visual structure.

## Timing

The first implementation should use a deterministic simulation clock/provider:

```text
attack launch → delivery: configurable short delay
website navigation: short bounded transition
credential submission: safe state transition, then outcome
MFA prompts: deterministic gaps
```

Use `instant`, `short`, and `standard` profiles. Tests must use `instant` or a
fake clock and must not sleep for realism.

## State Model

Target state relationships:

```text
AttackRun
  ├── operator context
  ├── victim context/session
  ├── lifecycle status
  ├── channel
  ├── delivery state
  ├── scenario-specific workflow state
  └── safe Event references

Session
  └── victim/operator correlation

Event
  └── immutable server timestamp and safe metadata
```

Credential values never enter any of these records.

## Security Verification

Required invariants for the reconstruction:

- no submitted password persistence, logging, broadcast, or replay;
- no external email/SMS delivery;
- no real organization, domain, account, or authentication endpoint;
- no executable attachment or arbitrary file/process execution;
- local-only redirects, QR destinations, and victim links;
- fictional parody content only;
- safe Event metadata with boolean credential facts;
- opaque local victim tokens with no secrets;
- no external assets, telemetry, or network egress.

## Original Gaps Before Implementation (Audit Baseline)

- The operator/victim context boundary does not yet exist.
- Delivery scheduling and message instances do not yet exist.
- Website workflows are still too uniform.
- Processing states and delayed reveals are incomplete.
- The standard live two-tab demonstration is not yet proven.
- Desktop-browser visual verification remains dependent on browser availability.

## Implementation Acceptance

The pass is complete only when a user can:

1. Open a victim's ordinary fictional inbox and leave it open.
2. Open `/lab` in another tab.
3. Launch a specific attack.
4. See an attack lifecycle and delivery status in the operator view.
5. See a new unread victim message after a deterministic delay.
6. Open a rich message and follow a scenario-specific workflow.
7. Interact with a believable service or channel mechanism.
8. Receive a branded service landing/home page and a scenario-specific training
   reveal, with a safe end-simulation control available.
9. Inspect the complete Event/indicator timeline in `/console`.

The same standard must hold for email, SMS, QR, attachment, MFA, and BEC flows,
with mechanisms that are meaningfully different rather than cosmetic variants.

## Implemented Reconstruction (2026-09-25)

The audit baseline above is retained as the before-state. The following changes
are now present in the working tree and are covered by the realism regression
tests.

### Reconstructed flow

```text
Open /mail or /messages
        ↓
persistent empty baseline environment receives an opaque local context cookie
        ↓
open /lab in another tab and launch
        ↓
operator receives an ARMED attack/status page; victim is not navigated to
        ↓
deterministic due time passes
        ↓
victim polling endpoint observes delivery
        ↓
new unread attack artifact appears in the pre-opened environment
        ↓
ENGAGED interaction emits safe Events
        ↓
branded service landing/home page and scenario-specific CTA
        ↓
site-specific verification or confirmation
        ↓
training reveal and COMPLETED state
        ↓
REST/WebSocket console timeline contains the complete sequence
```

### State and ownership

- `SimulationEnvironment` persists the pre-opened fictional mailbox/messaging
  context and its dedicated Session.
- `SimulationAttack` persists the opaque environment token, operator Session,
  victim Session, lifecycle status, due/delivered/engaged/completed timestamps,
  and allowlisted safe JSON state.
- `SimulationRun` remains available for legacy channel compatibility; the new
  victim routes use `SimulationAttack` as the incident source of truth.
- The operator Session remains the Event correlation Session. The dedicated
  victim Session is retained as environment identity and is completed with the
  incident. This preserves existing console grouping while keeping the victim
  route independent of the operator cookie.
- `DRAFT`, `ARMED`, `LAUNCHING`, `DELIVERED`, `ENGAGED`, `COMPLETED`,
  `ABANDONED`, `EXPIRED`, and `BLOCKED` are explicit validated states. The
  normal launch path arms immediately; `LAUNCHING` remains available for a
  future staged launcher.

### Delivery and timing

- `instant` = 0 ms, `short` = 1200 ms, and `standard` = 2400 ms.
- Tests never sleep: they use `instant` or move the persisted due timestamp
  directly, then request the victim status endpoint.
- Victim tabs poll the local context status endpoint. The browser uses safe DOM
  text APIs and reloads only when lifecycle/state changes; delivery includes a
  local notification toast.
- Each attack delivery has its own `attack_id`-backed `delivery_id`. Repeated
  launches of the same email or SMS scenario therefore render separate cards
  with their actual UTC delivery timestamps; artifact IDs remain the content
  identity, not the visible-instance identity. Read/open state remains scoped
  to the attack.
- SMS conversation cards use a boolean unread state and display `UNREAD`
  without a fabricated message count.
- QR, MFA, and website contexts use the same attack state boundary.

### Workflow coverage

| Flow                      | Implemented mechanism                                      | Processing/reveal behavior                      |
| ------------------------- | ---------------------------------------------------------- | ----------------------------------------------- |
| Email credential phishing | Gemail message → local link → UniSecure student flow       | password attempt → branded debrief              |
| SMS smishing              | QuickChat thread → local link → Amazaun                    | site-specific confirmation/result path          |
| Shopping/payment          | Address or billing confirmation instead of password        | non-credential victim action Event              |
| BEC                       | Executive/invoice lure → PayMate review                    | payment confirmation → reveal                   |
| Academic portals          | MAKExam registration ID and TechnoSphere course-code flows | distinct fictional labels and result copy       |
| Support                   | Employee ID and verification-code flow                     | support-specific landing and debrief            |
| CloudBox                  | Work-email terminology and storage context                 | password attempt remains boolean-only           |
| QR                        | Local QR image → explicit simulated scan                   | scan Event → target site                        |
| Attachment                | Inert attachment card and preview                          | no download, file, or execution                 |
| Link spoofing             | Visible/local destination preview                          | local link only; mismatch evidence remains safe |
| MFA fatigue               | Repeated NimbusID prompts with approve/deny                | terminal prompt → reveal                        |

### Verification evidence

Automated verification after the reconstruction:

- `174 passed, 1 warning` with the repository's in-memory SQLite test fixture.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed.
- `uv run pyright` passed with zero errors.
- `uv run check` is the final combined command and is recorded in the handoff
  after the last test run.
- `GET /health` now returns `200 {"status":"ok"}` for local process checks.
- Manual local HTTP/TestClient smoke flows A–F passed:
  - A: pre-opened mailbox → delayed email → branded site landing → reveal →
    analysis timeline;
  - B: pre-opened QuickChat → delayed SMS → Amazaun site;
  - C: delayed QR context → scan;
  - D: three repeated MFA prompts;
  - E: attachment preview with no download;
  - F: BEC invoice → PayMate confirmation, with
    `victim_action_completed` and no credential-submission Event.

### Security verification

- Credential form values are converted to boolean presence facts and are not
  stored in `SimulationAttack`, `SimulationRun`, Events, analysis, WebSocket
  payloads, logs, or response HTML.
- `credential_submission_attempted` retains the existing strict metadata schema;
  no raw value or extra credential-shaped field is added.
- All victim, QR, attachment, and service destinations are local routes with
  reserved `.example` hosts.
- No SMTP/SMS provider, external authentication, executable attachment,
  process/file execution, shell endpoint, external asset, or outbound network
  call was added.
- The opaque context token contains no identity or credential and is only a
  local simulation selector.

### Legacy SQLite compatibility fix

A real local database created by the first realism-pass schema could retain
SQLite unique indexes on `victim_session_id` and `victim_token`. Those indexes
prevented a single pre-opened victim environment from launching multiple
attacks, even though the current model intentionally shares that environment
Session/context.

`initialize_database()` now performs an idempotent, local-only SQLite upgrade
after `create_all()`:

- detects the obsolete single-column unique indexes;
- rebuilds only `simulation_attacks` using the current model;
- copies every existing row and timestamp unchanged;
- recreates the intended indexes;
- leaves an already-current database unchanged.

The upgrade is covered by
`tests/platform/test_schema_migration.py` and was verified against a copied
legacy-shaped database by launching both email and SMS attacks against the
same pre-opened environment. Existing local data does not need to be deleted.
Restart the application once after pulling this fix so startup can run the
migration.

- Desktop-browser visual/accessibility verification is still deferred because
  no connected browser was available; HTTP rendering, route behavior, and
  JavaScript syntax/security tests are covered.
- Legacy direct routes such as `/inbox` and `/sms` remain compatibility surfaces;
  the realistic two-tab path is `/mail` or `/messages` plus `/lab`.
- Delivery is request/poll driven rather than a background scheduler. This is
  intentional for a deterministic local lab and avoids long sleeps in tests.
- A general-purpose production migration framework and multi-user authorization
  remain outside the local single-operator safety scope; the targeted SQLite
  compatibility migration above is intentionally kept small and local.
- Real providers, real targets, credential replay, malware, and external
  telemetry remain intentionally prohibited rather than deferred features.

## Acceptance Status

The acceptance scenario is implemented and covered by automated and local HTTP
checks: a baseline mailbox/SMS environment can exist before launch, an operator
can launch and watch an armed attack, delivery changes that environment after a
deterministic delay, the victim follows a channel-specific workflow, processing
precedes the training reveal, and the analyst timeline contains the resulting
safe Events. Browser-based visual confirmation is the only outstanding
environment-dependent check.
