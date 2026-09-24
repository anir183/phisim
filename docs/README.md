# PhiSim Documentation

PhiSim is a local security-awareness and phishing-simulation lab. It
demonstrates common phishing patterns through fictional, inert
simulations and records security telemetry for an analyst console.

The project is intentionally designed as a **simulation**, not as a real
phishing platform.

## Documentation map

  ------------------------------------------------------------------------
  Document                             Purpose
  ------------------------------------ -----------------------------------
  [PLAN.md](PLAN.md)                   What will be implemented, in what
                                       priority, with acceptance criteria
                                       and team ownership

  [ARCHITECTURE.md](ARCHITECTURE.md)   Feature-oriented architecture,
                                       component boundaries, contracts,
                                       and project structure

  [CODE_STYLE.md](CODE_STYLE.md)       Python/code organization,
                                       modularity, simplicity,
                                       reliability, and testing
                                       conventions

  [GIT_MANNERS.md](GIT_MANNERS.md)     Branching, ownership, commits,
                                       integration, and
                                       conflict-minimization rules

  [AI.md](AI.md)                       Operating instructions for AI
                                       coding agents and the canonical
                                       project map

  [CONTRIBUTING.md](CONTRIBUTING.md)   Cross-platform setup and human/AI
                                       development workflow

  [SECURITY.md](SECURITY.md)           Safety boundary for all simulations
                                       and development

  [DECISIONS.md](DECISIONS.md)         Short record of important
                                       architectural decisions

  [ai/](ai/)                           AI-agent planning and workstream
                                       files; these are the only project
                                       docs AI agents may edit
  ------------------------------------------------------------------------

## Priority

The first user-visible simulation milestone is:

1.  **Fake credential site**
2.  **Email phishing simulation**
3.  **SMS/smishing simulation**

After that, the remaining scenario catalogue is implemented
incrementally:

-   spear phishing
-   whaling
-   clone phishing
-   urgency phishing
-   tech-support phishing
-   QR phishing / quishing
-   attachment phishing
-   link spoofing
-   business email compromise simulation
-   MFA-fatigue simulation

These scenarios should reuse common simulation, telemetry, analysis, and
presentation primitives rather than becoming independent
mini-applications.

## Current implementation

The repository already contains:

-   FastAPI application startup
-   environment settings through `pydantic-settings`
-   SQLite/SQLAlchemy infrastructure
-   event persistence
-   `POST /api/events`
-   WebSocket event broadcasting
-   an initial analyst console
-   project scripts for development, testing, linting, formatting, and
    type checking
-   a `src/phisim` namespace-package layout
-   shared web templates/static directories

The documentation describes the intended next architecture without
pretending that planned modules already exist.

## Development principle

Keep the system boring:

> Small modules, explicit data contracts, shared primitives, few
> abstractions, deterministic behavior, and tests around boundaries.

If a feature can be implemented by composing an existing service,
schema, repository, template, or utility, do that before introducing
another abstraction.

## Safety boundary

All simulations must remain:

-   local/loopback by default
-   fictional
-   inert
-   non-persistent with respect to submitted credentials
-   free of real outbound email/SMS delivery
-   free of malware or executable payloads
-   free of shell/file-execution endpoints
-   free of real organization branding or accounts
-   safe to run as a classroom project

See [SECURITY.md](SECURITY.md) for the complete boundary.
