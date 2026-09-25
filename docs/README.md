# PhiSim Documentation

PhiSim is a local security-awareness and phishing-simulation lab. It demonstrates recognizable phishing patterns through fictional applications and records safe, explainable telemetry for an analyst console.

PhiSim is deliberately a simulation. It does not send real messages, contact real providers, collect usable credentials, or target real organizations.

## Start here

- [Project README](../README.md) — setup, commands, routes, and architecture overview
- [Architecture](ARCHITECTURE.md) — subsystem boundaries and data flow
- [Security and safety](SECURITY.md) — non-negotiable simulation boundary
- [Contributing](CONTRIBUTING.md) — local setup and development workflow
- [Code style](CODE_STYLE.md) — project conventions and review expectations
- [Decisions](DECISIONS.md) — architectural decisions and rationale

## Current implementation

The repository currently includes:

- FastAPI application startup and a loopback-safe development server
- SQLite/SQLAlchemy persistence for scenarios, sessions, events, and simulation state
- deterministic local delivery for email, SMS, QR, MFA, and website scenarios
- branded Gemail, QuickChat, Amazaun, CloudBox, university, support, payment, MFA, and QR experiences
- product-specific post-action destination pages and an explicit manual-end transition
- a separate operator Lab, analyst Console, and training Reveal
- safe event persistence, analysis indicators, inspection timelines, and WebSocket updates
- focused platform, simulation, security, UI, and live-update tests

The normal participant path is:

```text
Lab launch
  → local delivery
  → fictional victim application
  → meaningful interaction
  → product-specific destination
  → explicit End simulation
  → training Reveal
  → analyst evidence and indicators
```

## Documentation map

### Project and contribution docs

| Document                           | Purpose                                                   |
| ---------------------------------- | --------------------------------------------------------- |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Application layers, contracts, and repository structure   |
| [CODE_STYLE.md](CODE_STYLE.md)     | Python style, modularity, typing, and testing conventions |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Tooling, environment setup, commands, and review workflow |
| [GIT_MANNERS.md](GIT_MANNERS.md)   | Branching, ownership, commits, and integration rules      |
| [SECURITY.md](SECURITY.md)         | Credential, network, attachment, and privacy boundaries   |
| [DECISIONS.md](DECISIONS.md)       | Recorded architectural decisions                          |
| [PLAN.md](PLAN.md)                 | Historical implementation priorities and milestones       |
| [AI.md](AI.md)                     | AI-agent operating rules and project map                  |

### UI and verification records

| Document                                                       | Purpose                                              |
| -------------------------------------------------------------- | ---------------------------------------------------- |
| [ai/UI_REALISM_AUDIT.md](ai/UI_REALISM_AUDIT.md)               | Initial application-boundary and realism audit       |
| [ai/UI_REALISM_TEST_REPORT.md](ai/UI_REALISM_TEST_REPORT.md)   | Automated and route-level verification evidence      |
| [ai/UI_REALISM_FINAL_REPORT.md](ai/UI_REALISM_FINAL_REPORT.md) | Final UI status, limitations, and acceptance summary |

### Workstream notes

The files under [`ai/`](ai/) retain focused backend, simulation, analysis, console, and integration notes. They are implementation history and coordination context; the source tree and the canonical project documents above are authoritative when they disagree.

## Documentation maintenance

- Keep the root [README](../README.md) concise and task-oriented.
- Keep architectural and safety rules in the canonical documents listed above.
- Update verification counts and limitations when the implementation changes.
- Prefer deleting stale handoff notes over preserving contradictory status pages.
- Old integration handoff reports were removed; use the current architecture,
  security, and UI verification documents instead.
- Do not add generated reports, temporary screenshots, or scratch notes to `docs/`.

## Safety boundary

All changes must preserve these properties:

- local/loopback operation by default
- fictional organizations, identities, messages, and domains
- no real outbound email or SMS
- no credential or payment-detail persistence
- no external provider or network dependency
- inert attachments and local-only QR targets
- no shell, code, or arbitrary-file execution
- safe, allowlisted telemetry only

See [SECURITY.md](SECURITY.md) before changing simulation, telemetry, or browser behavior.
