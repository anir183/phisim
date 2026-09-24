# AI Agent Instructions

This document is the operating contract for AI coding agents working on
PhiSim.

## 1. Canonical documentation rule

There are two documentation namespaces:

``` text
docs/*.md       canonical human/project documentation
docs/ai/*.md    AI planning/interface documentation
```

### Mandatory restriction

AI agents:

-   **MUST NOT edit any `docs/*.md` file**
-   **MAY edit only `docs/ai/*.md` for AI planning/interface artifacts**
-   MUST treat existing `docs/*.md` as read-only project policy

If a human asks an AI agent to change canonical documentation, the human
should make that change directly or explicitly perform the
documentation-editing task outside the normal coding-agent workflow.

AI agents may read all documentation.

------------------------------------------------------------------------

## 2. Source of truth

For application behavior, prefer the actual source tree over stale
planning notes.

For project policy:

``` text
docs/*.md
```

is canonical.

For active AI task coordination:

``` text
docs/ai/*.md
```

is the coordination layer.

If the code and documentation disagree:

1.  do not silently rewrite either one;
2.  report the discrepancy;
3.  implement only the requested scope;
4.  record the required documentation follow-up in the relevant
    `docs/ai/*.md`.

------------------------------------------------------------------------

## 3. Project map

``` text
src/phisim/
├── analysis/       # structured phishing/interaction analysis
├── console/        # analyst-facing routes and presentation integration
├── infra/          # persistence and infrastructure implementations
├── inspection/     # event/session inspection and explanations
├── security/       # safety/security guardrails
├── simulation/     # phishing simulation behavior
├── telemetry/      # event API and event broadcasting
├── utils/          # small genuinely shared utilities
└── main.py         # application composition

web/
├── templates/      # Jinja/browser templates
└── static/         # browser CSS/JS/assets

scenarios/          # scenario data/assets

tests/              # automated tests

scripts/            # developer command entry points

tools/              # optional developer helpers

data/               # local runtime data, not source code

docs/               # canonical human documentation
docs/ai/            # AI-only planning/interface notes
```

------------------------------------------------------------------------

## 4. Current application entry point

The FastAPI application is:

``` text
phisim.main:app
```

The project exposes:

``` text
phisim
dev
test
lint
format
typecheck
check
clean
```

The preferred commands are:

``` bash
uv run dev
uv run test
uv run lint
uv run format
uv run typecheck
uv run check
```

The normal development server uses the configured host and port from the
project settings.

Environment configuration uses:

``` text
PHISIM_ENV
PHISIM_HOST
PHISIM_PORT
PHISIM_DB_URL
```

See `.env.example`.

------------------------------------------------------------------------

## 5. Do not assume files exist

Before implementing a planned module:

1.  inspect the current tree;
2.  inspect the owning subsystem;
3.  inspect existing tests;
4.  reuse current contracts;
5.  only then create the new file.

Planning documents describe intended architecture, not guaranteed
implementation.

------------------------------------------------------------------------

## 6. Correct place for new code

Use the narrowest appropriate subsystem.

  ---------------------------------------------------------------------
  Need                               Location
  ---------------------------------- ----------------------------------
  event API                          `src/phisim/telemetry/`

  DB model/repository                `src/phisim/infra/sqlite/`

  simulation behavior                `src/phisim/simulation/`

  scenario assets                    `scenarios/`

  indicator logic                    `src/phisim/analysis/`

  inspection/explanation             `src/phisim/inspection/`

  security guardrail                 `src/phisim/security/`

  analyst UI backend                 `src/phisim/console/`

  console browser assets             `web/templates/console/`,
                                     `web/static/console/`

  simulation browser assets          `web/templates/simulation/`,
                                     `web/static/simulation/`

  tiny cross-cutting helper          `src/phisim/utils/`

  tests                              matching `tests/` area
  ---------------------------------------------------------------------

Do not create new top-level directories without a documented reason.

------------------------------------------------------------------------

## 7. AI workflow

Every AI task should follow:

``` text
read docs
  -> inspect code
  -> read relevant docs/ai/*.md
  -> define owned files
  -> implement smallest change
  -> write/update tests
  -> run checks
  -> update only docs/ai/*.md if coordination changed
  -> summarize changed files and checks
```

Before editing, the agent should state internally or in its task record:

-   goal
-   owned files
-   contracts consumed
-   contracts changed
-   tests required
-   security implications

------------------------------------------------------------------------

## 8. Ownership

Follow the four workstreams:

### Team 1

``` text
src/phisim/infra/
src/phisim/telemetry/
src/phisim/utils/
```

### Team 2

``` text
src/phisim/simulation/
scenarios/
simulation web assets
```

### Team 3

``` text
src/phisim/analysis/
src/phisim/inspection/
src/phisim/security/
```

### Team 4

``` text
src/phisim/console/
console web assets
```

Avoid editing another team's owned files.

If another subsystem is required, depend on its public contract rather
than reaching into its internals.

------------------------------------------------------------------------

## 9. Code design rules

Prefer:

-   explicit functions
-   typed Pydantic contracts
-   thin FastAPI routes
-   repositories for DB access
-   small services
-   deterministic analysis
-   focused tests

Avoid:

-   speculative interfaces
-   generic frameworks
-   "manager of manager" abstractions
-   giant utility modules
-   global state for domain behavior
-   duplicated business rules
-   direct DB access from UI/simulation code

Do not refactor unrelated code while implementing a feature.

------------------------------------------------------------------------

## 10. Security constraints

PhiSim is a controlled educational simulation.

AI agents MUST NOT implement:

-   real credential harvesting
-   password persistence
-   credential replay
-   real SMTP/SMS delivery
-   public campaign infrastructure
-   malware
-   executable attachment delivery
-   shell execution endpoints
-   arbitrary file read/write endpoints
-   stealth/persistence mechanisms
-   real target lists
-   real organization impersonation
-   public-by-default binding

The application should remain local/loopback by default.

Credential submissions may generate:

``` text
credential_submission_attempted
```

but submitted secret values must never be stored or emitted as
telemetry.

------------------------------------------------------------------------

## 11. Scenario implementation rule

A scenario should be a composition of common primitives.

Do not create:

``` text
fake-site framework
email framework
sms framework
```

when one simulation/session/telemetry architecture can support all
three.

Scenario-specific differences belong in:

-   scenario metadata
-   templates
-   harmless content
-   interaction definitions
-   indicator configuration

------------------------------------------------------------------------

## 12. Analysis rule

Analysis should expose evidence.

Prefer:

``` text
domain_mismatch
evidence = "..."
explanation = "..."
```

over:

``` text
risk = 97
```

A score can be added later if it has a clear educational purpose and
documented semantics.

------------------------------------------------------------------------

## 13. Testing rule

AI agents should run the smallest relevant test first and the full check
before handing work back:

``` bash
uv run test
uv run check
```

If a full check cannot be run, say exactly which command failed and why.

Do not claim tests passed without actually running them.

------------------------------------------------------------------------

## 14. Dependency rule

Do not add a dependency for convenience.

If a dependency is required:

1.  explain why;
2.  check existing dependencies;
3.  ensure cross-platform compatibility;
4.  update the lockfile using `uv`.

------------------------------------------------------------------------

## 15. Optional AI tooling

AI tools may improve development, but they are optional.

Useful categories include:

-   repository-aware coding agents
-   IDE assistants
-   MCP servers for GitHub/issue tracking
-   documentation/search MCPs
-   browser automation for harmless UI testing
-   local test-running agents

Any AI/MCP tool must follow the same repository safety boundary.

Do not grant an AI tool access to real mail/SMS accounts or secrets for
PhiSim.

------------------------------------------------------------------------

## 16. AI planning files

The `docs/ai/` directory is the AI coordination layer.

Agents should use:

``` text
docs/ai/README.md
docs/ai/team-1-backend.md
docs/ai/team-2-simulation.md
docs/ai/team-3-analysis.md
docs/ai/team-4-console.md
docs/ai/integration.md
docs/ai/ai-task-template.md
```

These files may contain:

-   current task
-   owned paths
-   dependencies
-   contract notes
-   TODOs
-   phase state
-   test status
-   handoff notes

They are not a replacement for canonical project documentation.

------------------------------------------------------------------------

## 18. First 2--3 hour execution target

For the first collaborative implementation session, do not attempt to
finish every P0 feature.

The target is one complete vertical slice:

``` text
fake credential site
    -> session
    -> telemetry
    -> SQLite
    -> analysis
    -> WebSocket
    -> console
```

With four contributors working roughly 2--3 hours each, use this split:

-   Team 1: minimum Scenario/Session/Event backend contract
-   Team 2: fake credential site
-   Team 3: four basic indicators + credential-secret safety test
-   Team 4: live event/session console

Once that works, the next short run adds email and SMS.

## 19. Email/SMS implementation rule

Email and SMS are **local simulated interfaces**, not delivery systems.

### Email

Use:

``` text
FastAPI + Jinja2
    -> fake inbox
    -> fake email viewer
    -> local links/interactions
```

No SMTP server or email provider is required.

### SMS

Use:

``` text
FastAPI + Jinja2
    -> fake message conversation
    -> local links/interactions
```

No SMS gateway or carrier API is required.

The P0 implementation requires no new third-party dependency for either
channel.

Python's standard-library `email` package may be used later if
representing MIME/header structures is educationally useful.

Do not independently introduce Twilio, Vonage, AWS SNS, Gmail/Microsoft
APIs, SendGrid, Mailgun, Resend, SMTP credentials, phone-number lists,
or external recipients.

## 20. Final response format for coding agents

When an AI coding task is complete, report:

``` text
Changed:
- file
- file

Behavior:
- concise description

Tests:
- command -> result

Contracts:
- unchanged / changed

Security:
- relevant safety impact

Follow-up:
- optional next task
```

Do not dump large code excerpts unless requested.
