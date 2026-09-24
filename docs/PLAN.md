# PhiSim Implementation Plan

## 1. Goal

Build a local phishing-awareness lab in which a participant encounters
synthetic phishing artifacts, interacts with them in a controlled
browser, and receives telemetry and analysis in an analyst console.

The system should demonstrate both:

1.  **attack-pattern recognition** --- what a phishing artifact looks
    like; and
2.  **defensive telemetry** --- what a security-awareness platform could
    observe from the simulation.

No real phishing delivery is part of the project.

------------------------------------------------------------------------

## 2A. First 2--3 hour implementation run

The first team session is intentionally a **thin vertical slice**, not
an attempt to finish P0.

With four contributors working for roughly **2--3 hours each** (about
8--12 person-hours total), the target is:

``` text
fake credential site
      ↓
session
      ↓
credential_submission_attempted
      ↓
existing event API
      ↓
SQLite
      ↓
WebSocket
      ↓
analyst console
```

### Team 1 --- first run

**Goal:** stabilize the minimum backend contract.

1.  Confirm/fix `EventCreate` and `EventResponse`.
2.  Remove stale client-supplied `timestamp` from tests; timestamp
    remains server-generated.
3.  Add the minimum Scenario model/repository.
4.  Add the minimum Session model/repository.
5.  Expose only the endpoints needed for the first vertical slice.
6.  Add/maintain test fixtures.

**Do not spend this run on:**

-   migrations
-   PostgreSQL support
-   generic repository interfaces
-   large refactors
-   production deployment

### Team 2 --- first run

**Goal:** make the fake credential site usable.

1.  Add one fictional scenario.
2.  Render a local fake login page.
3.  Start/associate a session.
4.  Handle form submission safely.
5.  Emit `credential_submission_attempted`.
6.  Never include the submitted password in telemetry.
7.  Show a safe educational outcome after submission.

### Team 3 --- first run

**Goal:** provide the minimum explainable analysis.

Implement a small deterministic indicator set:

``` text
credential_request
urgent_language
domain_mismatch
authority_impersonation
```

The team can initially test against fixtures rather than waiting for
full end-to-end integration.

Also add the first security test proving that submitted passwords cannot
enter an event payload.

### Team 4 --- first run

**Goal:** turn the existing console into a useful first demo.

1.  Display the live event stream.
2.  Display scenario/session information.
3.  Display a simple event timeline.
4.  Render event values safely using DOM text APIs.
5.  Handle a missing/disconnected WebSocket without crashing the page.

### First-run definition of done

The first run is successful when a contributor can:

``` text
open local fake site
    → interact with fake login
    → submit fictional credentials
    → receive an educational outcome
    → observe an event in the console
    → see the event persisted in SQLite
    → see basic indicators
```

This is the first **functional PhiSim milestone**.

### Second 2--3 hour run

After the vertical slice works, reuse the exact same machinery for:

1.  **Email phishing**
2.  **SMS/smishing**

Neither requires a real delivery provider.

Email:

``` text
FastAPI
  → fake inbox
  → fake email viewer
  → local link
  → existing simulation/telemetry
```

SMS:

``` text
FastAPI
  → fake conversation
  → local message/link
  → existing simulation/telemetry
```

No SMTP, email provider, SMS gateway, Twilio, Vonage, AWS SNS, Gmail
API, Microsoft Graph, SendGrid, Mailgun, or Resend integration is
required for P0.

### P0 --- first integrated milestone

These are required before the team treats the simulation platform as
usable.

  Priority   Feature                                       Main owner
  ---------- --------------------------------------------- --------------------------
  P0         Fake credential/login site                    Team 2
  P0         Email phishing simulation artifact/workflow   Team 2
  P0         SMS/smishing simulation artifact/workflow     Team 2
  P0         Scenario/session lifecycle                    Team 1
  P0         Event telemetry contract and persistence      Team 1
  P0         Analyst console showing live events           Team 4
  P0         Basic indicator analysis                      Team 3
  P0         Shared scenario metadata/registry             Team 1 + contract review

### P1 --- expand the scenario catalogue

  Feature                          Main owner
  -------------------------------- ------------
  Spear phishing                   Team 2
  Whaling                          Team 2
  Clone phishing                   Team 2
  Urgency phishing                 Team 2
  Tech-support phishing            Team 2
  QR phishing / quishing           Team 2
  Attachment phishing              Team 2
  Link spoofing                    Team 2
  BEC simulation                   Team 2
  MFA-fatigue simulation           Team 2
  Richer indicator analysis        Team 3
  Session/scenario analytics       Team 3
  Console filtering/detail views   Team 4

### P2 --- polish and extension

Potential later work:

-   scenario authoring format
-   reusable message templates
-   richer analyst dashboards
-   export/import of simulation results
-   more detailed timeline analysis
-   accessibility improvements
-   fixture/demo-data generation
-   additional harmless channel simulations
-   optional container/dev tooling

P2 work must not destabilize P0 contracts.

------------------------------------------------------------------------

## 3. Priority model

The split is deliberately **directory-oriented**. Each member should
normally create and modify files in their owned area only.

### Team 1 --- Platform / backend / persistence

**Owns**

``` text
src/phisim/main.py
src/phisim/telemetry/
src/phisim/infra/
src/phisim/utils/
tests/test_repository.py
tests/telemetry/
tests/platform/
```

**Responsibilities**

-   application startup/lifespan
-   event API
-   WebSocket manager
-   scenario/session persistence
-   repositories
-   database models
-   environment/configuration
-   backend-level validation
-   integration tests for backend contracts

**Primary deliverables**

1.  Scenario model/repository/API
2.  Session model/repository/API
3.  Event/session relationship
4.  stable event contract
5.  stable scenario metadata contract
6.  test fixtures for other teams

**Does not own**

-   phishing page/message presentation
-   indicator rules
-   analyst dashboard UI

------------------------------------------------------------------------

### Team 2 --- Simulation channels

**Owns**

``` text
src/phisim/simulation/
scenarios/
web/templates/simulation/
web/static/simulation/
tests/simulation/
```

If the exact template/static subtree is not present yet, Team 2 may
create it under the existing `web/templates` and `web/static` roots.

**Responsibilities**

-   fake credential site
-   email simulation
-   SMS simulation
-   later phishing scenarios
-   common simulation rendering
-   safe interaction handlers
-   scenario-specific telemetry emission
-   harmless QR generation
-   inert attachment examples

**Primary deliverables**

1.  common scenario interface/loader only if actually necessary
2.  fake login flow
3.  email artifact
4.  SMS artifact
5.  scenario templates
6.  scenario-specific tests

**Critical rule**

Team 2 does not directly modify database models or the analyst console
to make a scenario work. It emits the agreed telemetry contract.

------------------------------------------------------------------------

### Team 3 --- Analysis / inspection / security

**Owns**

``` text
src/phisim/analysis/
src/phisim/inspection/
src/phisim/security/
tests/analysis/
tests/inspection/
tests/security/
```

**Responsibilities**

-   phishing-indicator extraction
-   event/session analysis
-   risk/indicator classification
-   explanation of why an artifact is suspicious
-   security-policy enforcement helpers
-   input validation that is specifically security-oriented
-   analysis tests

**Primary deliverables**

1.  indicator model
2.  rule-based indicator engine
3.  event-to-analysis pipeline
4.  scenario-aware indicator explanations
5.  security guardrails
6.  analysis fixtures

The analysis layer should produce structured facts, not a vague single
score.

------------------------------------------------------------------------

### Team 4 --- Analyst console / presentation / integration UX

**Owns**

``` text
src/phisim/console/
web/templates/console/
web/static/console/
tests/console/
```

**Responsibilities**

-   analyst console
-   live event stream
-   session timeline
-   scenario/session detail
-   filtering
-   indicator presentation
-   safe DOM rendering
-   browser-facing integration tests

**Primary deliverables**

1.  live event view
2.  session timeline
3.  scenario metadata view
4.  event detail view
5.  indicator/explanation panel
6.  basic filtering

Team 4 consumes APIs/contracts. It should not reach directly into
SQLAlchemy models.

------------------------------------------------------------------------

## 4. Shared-contract protocol

The team split is only effective if shared contracts are treated as
APIs.

### Contract owners

-   Team 1 owns persistence/API contracts.
-   Team 2 owns scenario interaction semantics.
-   Team 3 owns analysis result structures.
-   Team 4 owns presentation needs, but cannot silently redefine backend
    contracts.

A contract change requires:

1.  a small design note in the relevant `docs/ai/*.md` work file while
    actively being developed;
2.  an explicit PR/commit description;
3.  tests for the changed contract;
4.  notification to all affected owners;
5.  no unrelated refactoring in the same change.

Canonical public contracts should eventually be represented by Pydantic
schemas rather than copied dictionaries.

------------------------------------------------------------------------

## 5. Implementation phases

### Phase 0 --- contract stabilization

**Goal:** make parallel work safe.

-   finalize event schema
-   finalize scenario schema
-   finalize session schema
-   define event type naming
-   define telemetry metadata conventions
-   define simulation-to-telemetry boundary
-   define analysis output shape
-   clean stale tests
-   document safety constraints

**Exit condition:** all four teams can work without modifying one
another's implementation files.

### Phase 1 --- P0 vertical slice

Build one complete flow:

``` text
scenario
  -> fake login page
  -> interaction
  -> event
  -> persistence
  -> analysis
  -> WebSocket
  -> console
```

Then add email and SMS using the same platform primitives.

### Phase 2 --- scenario expansion

Implement P1 scenarios by composing the existing simulation primitives.

### Phase 3 --- analyst experience

Improve filtering, timelines, explanations, and session views.

### Phase 4 --- reliability/polish

-   error handling
-   idempotency
-   accessibility
-   test coverage
-   browser compatibility
-   safe shutdown
-   documentation
-   fixture/demo data

------------------------------------------------------------------------

## 6. Definition of done

A feature is not complete because its page renders.

A scenario is done when:

-   it is fictional and inert;
-   it has a scenario identifier;
-   it can be launched in a local session;
-   meaningful interactions generate telemetry;
-   no secret submitted by the participant is stored;
-   events persist correctly;
-   the analyst console can observe the interaction;
-   analysis produces structured indicators where applicable;
-   the scenario has automated tests;
-   the scenario has no outbound delivery path;
-   the feature follows the ownership and Git rules.

------------------------------------------------------------------------

## 7. Testing levels

Every feature should have the smallest useful tests at multiple
boundaries.

### Unit

Pure logic:

-   indicator extraction
-   scenario validation
-   message construction
-   identifier generation
-   analysis rules

### Integration

Component boundaries:

-   API -\> service -\> repository
-   simulation -\> telemetry
-   telemetry -\> analysis
-   WebSocket -\> console

### Browser/manual

Only for actual UI behavior:

-   fake login interaction
-   email artifact rendering
-   SMS artifact rendering
-   console live update
-   responsive layout

------------------------------------------------------------------------

## 8. Suggested event taxonomy

Use stable, descriptive names.

Examples:

``` text
session_started
session_completed
scenario_opened
scenario_interaction
link_clicked
credential_submission_attempted
message_opened
attachment_opened
qr_viewed
mfa_prompt_displayed
mfa_prompt_responded
analysis_completed
```

A credential submission event must contain **no password value**.

Do not invent dozens of event types when a typed metadata field can
represent a variation.

------------------------------------------------------------------------

## 9. What not to build

Do not add:

-   real SMTP sending
-   real SMS gateways
-   public campaign delivery
-   real credential harvesting
-   password storage
-   credential replay
-   malware or executable payloads
-   shell execution from HTTP requests
-   arbitrary server-side file access
-   stealth/persistence mechanisms
-   real-world target lists

The classroom value comes from simulation and analysis, not real
delivery capability.
