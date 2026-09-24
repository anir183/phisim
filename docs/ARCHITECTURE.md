# PhiSim Architecture

## 1. Architectural goal

PhiSim is a small modular web application with four logical layers:

``` text
Simulation
    |
    v
Telemetry
    |
    +----> Persistence
    |
    +----> Analysis / Inspection
    |
    v
Analyst Console
```

The important design rule is:

> Simulation code emits events. It does not know how events are stored
> or displayed.

Similarly:

> The console consumes API/event contracts. It does not access database
> models directly.

------------------------------------------------------------------------

## 2. Current repository structure

``` text
src/phisim/
├── analysis/          # indicator and event analysis
├── console/           # analyst-facing HTTP/UI integration
├── infra/
│   └── sqlite/        # SQLAlchemy engine, models, repositories
├── inspection/        # inspection/explanation helpers
├── security/          # security-specific guardrails/validation
├── simulation/        # simulated phishing channels and interactions
├── telemetry/         # event API, services, WebSocket broadcasting
├── utils/             # small shared utilities/config/path helpers
└── main.py            # FastAPI application composition

web/
├── static/            # browser assets
└── templates/         # Jinja templates

scenarios/             # scenario definitions/assets/fixtures

tests/                 # automated tests mirroring major boundaries

scripts/
└── runners.py         # project command entry points

tools/                 # developer-only helper tooling

docs/
└── ai/                # AI-agent planning/interface notes
```

The existing repository also contains the SQLite database under `data/`.

------------------------------------------------------------------------

## 3. Feature architecture

### 3.1 Scenario lifecycle

A scenario is metadata plus a simulation experience.

Conceptually:

``` text
Scenario
  ├── identity
  ├── type
  ├── description
  └── presentation/configuration

Session
  ├── scenario_id
  ├── lifecycle
  └── events

Event
  ├── event_id
  ├── timestamp
  ├── session_id
  ├── scenario_id
  ├── event_type
  ├── source
  └── metadata
```

Scenario definitions should not contain persistence logic.

------------------------------------------------------------------------

## 4. Telemetry

The telemetry subsystem is the system's internal event boundary.

``` text
simulation
    |
    | EventCreate
    v
POST /api/events
    |
    v
TelemetryService
    |
    +--> repository
    |
    +--> WebSocket broadcaster
```

The current implementation already has:

-   `EventCreate`
-   `EventResponse`
-   event repository
-   duplicate event detection
-   event persistence
-   WebSocket broadcasting

Future work should extend this rather than bypass it.

### Event contract

The event should have:

``` text
event_id
session_id
scenario_id
event_type
source
metadata
timestamp (server-generated)
```

`metadata` contains event-specific facts.

Secrets do not belong in `metadata`.

------------------------------------------------------------------------

## 5. Persistence

SQLite/SQLAlchemy is the current persistence layer.

The intended structure is:

``` text
infra/sqlite/
├── connection.py
├── models_registry.py
├── models/
│   ├── event.py
│   ├── scenario.py
│   └── session.py
└── repos/
    ├── event.py
    ├── scenario.py
    └── session.py
```

Repositories isolate SQLAlchemy queries from application services.

Do not create a generic repository abstraction merely to avoid three
small repositories. Explicit repositories are easier to understand and
test.

------------------------------------------------------------------------

## 6. Simulation subsystem

The simulation layer should provide reusable primitives for:

-   scenario loading
-   session start
-   artifact rendering
-   interaction handling
-   telemetry emission
-   completion state

Priority channels:

``` text
P0
├── fake credential site
├── email
└── SMS

P1
├── spear phishing
├── whaling
├── clone phishing
├── urgency
├── tech support
├── QR/quishing
├── attachment
├── link spoofing
├── BEC
└── MFA fatigue
```

### Fake credential site

The page may contain a fake username/password form for educational
realism.

On submission:

``` text
credential_submission_attempted
```

The event must not include the submitted password.

The browser should then transition to an educational outcome page or
equivalent safe state.

### Email simulation

Email is represented as an inert simulated message inside a local PhiSim
mailbox.

The P0 implementation does **not** send email. It does not require SMTP,
an SMTP server, Gmail/Microsoft APIs, SendGrid, Mailgun, Resend, or any
other external mail provider.

The first implementation is simply:

``` text
FastAPI
   |
Jinja2/local templates
   |
Fake inbox
   |
Fake email viewer
   |
link/interaction
   |
existing simulation + telemetry
```

A simulated email may contain:

-   fictional sender
-   fictional subject
-   body text
-   local links
-   harmless attachment representations

If RFC/MIME parsing becomes educationally useful later, Python's
standard-library `email` package may be used. It is not required for P0.

Possible interactions:

``` text
message_opened
link_clicked
attachment_opened
```

No SMTP transport is required.

### SMS simulation

SMS is represented as an inert simulated message/conversation inside
PhiSim.

The P0 implementation does **not** send SMS. It does not require Twilio,
Vonage, AWS SNS, Firebase messaging, a carrier API, phone-number lists,
or any external SMS provider.

The first implementation is simply:

``` text
FastAPI
   |
Jinja2/local templates
   |
Fake conversation UI
   |
link/interaction
   |
existing simulation + telemetry
```

No phone number is contacted. A sender can be represented by fictional
text such as `Delivery Service` or a synthetic number.

No carrier or SMS gateway is required.

------------------------------------------------------------------------

## 7. Shared channel model

Email, SMS, and the fake credential site are **channels of the same
simulation system**, not three independent applications.

``` text
                    Scenario
                       |
          +------------+------------+
          |            |            |
       Website       Email         SMS
          |            |            |
          +------------+------------+
                       |
                  Interaction
                       |
                   Telemetry
                       |
             +---------+---------+
             |                   |
          SQLite             Analysis
             |                   |
             +---------+---------+
                       |
                    Console
```

Channel-specific code should primarily describe presentation and
interaction semantics. Session management, event emission, persistence,
analysis, and console integration remain shared.

### P0 package rule

No new dependency is required specifically for email or SMS.

The existing stack is sufficient:

``` text
FastAPI
Jinja2
Pydantic
SQLAlchemy + SQLite
WebSocket
```

Use Python's standard library before adding another dependency.

## 8. Analysis subsystem

Analysis converts raw events and scenario metadata into structured
observations.

Prefer:

``` text
Indicator
  ├── code
  ├── category
  ├── severity/context
  ├── evidence
  └── explanation
```

over a single opaque "phishing score".

Examples:

``` text
urgent_language
credential_request
unexpected_link
domain_mismatch
authority_impersonation
suspicious_attachment_name
unusual_mfa_request
```

Analysis should be deterministic and testable.

------------------------------------------------------------------------

## 9. Inspection subsystem

Inspection answers:

> What happened, and what evidence should a learner/analyst inspect?

It can consume:

-   scenario metadata
-   events
-   analysis results

It should not duplicate analysis rules.

If analysis says:

``` text
domain_mismatch
```

inspection may explain the evidence and display it, but the rule belongs
in analysis.

------------------------------------------------------------------------

## 10. Security subsystem

Security contains guardrails that protect the simulation itself.

Examples:

-   loopback/default host enforcement
-   safe redirect validation
-   forbidden payload/file checks
-   secret stripping
-   input normalization
-   simulation-only restrictions

Security helpers should be small and explicit.

Do not build a generic policy framework unless a concrete requirement
demands one.

------------------------------------------------------------------------

## 11. Analyst console

The console is a consumer of backend contracts.

``` text
HTTP page
   +
WebSocket event stream
   +
REST/API reads
   |
   v
Analyst UI
```

The console should eventually provide:

-   active sessions
-   scenario information
-   event timeline
-   event detail
-   indicator explanations
-   basic filtering

### Browser security

Do not insert untrusted event data into `innerHTML`.

Use DOM text APIs or framework-safe rendering.

Event metadata should also be treated as untrusted input even though the
application generates most events.

------------------------------------------------------------------------

## 12. Application composition

`main.py` should remain a composition root.

It should:

-   create the FastAPI application
-   register routers
-   initialize lifecycle resources

It should not become the place where business logic is implemented.

------------------------------------------------------------------------

## 13. Dependency direction

Prefer this direction:

``` text
web / routes
      |
      v
application services
      |
      +------> repositories
      |
      +------> analysis
      |
      v
domain/application schemas

infra sits below services.
simulation emits into application boundaries.
console consumes application boundaries.
```

Avoid circular dependencies such as:

``` text
console -> simulation -> console
analysis -> console
repository -> service
```

------------------------------------------------------------------------

## 14. Shared utilities

`utils/` is for genuinely cross-cutting small helpers.

Do not put domain logic there merely because it is used twice.

Before adding a utility:

1.  prove the logic is actually duplicated;
2.  give it a clear name;
3.  keep it dependency-light;
4.  add a focused test if behavior is non-trivial.

------------------------------------------------------------------------

## 15. Web assets

Use separate namespaces under the shared web roots:

``` text
web/templates/
├── console/
└── simulation/

web/static/
├── console/
└── simulation/
```

This prevents the four team members from constantly editing one giant
template or stylesheet.

------------------------------------------------------------------------

## 16. External boundaries

PhiSim intentionally has no required external delivery boundary.

The safe default is:

``` text
browser
  |
127.0.0.1
  |
FastAPI
  |
SQLite
```

Email/SMS are simulated internally.

If future research adds another integration, it must be opt-in,
documented, and reviewed against the security boundary before
implementation.
