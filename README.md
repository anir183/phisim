# PhiSim

PhiSim is a local, fictional phishing-awareness lab. It lets a participant move through believable mailbox, messenger, marketplace, storage, academic, support, payment, QR, and MFA experiences while an analyst console records safe, explainable telemetry.

PhiSim is a **simulation**, not a phishing platform. It does not send email or SMS, contact real providers, collect usable credentials, execute attachments, or target real organizations.

## Quick start

### Requirements

- Python 3.14+
- [`uv`](https://docs.astral.sh/uv/)
- Git

### Install and run

```bash
git clone <repository-url>
cd phisim
uv sync
cp .env.example .env
uv run dev
```

The example environment enables the opt-in synthetic sandbox capture used by
the local training demo. It accepts only allowlisted demo values: emails
ending in `@example.com` or `@gemail.com`, fictional payment options, and
training-prefixed secret fields such as `sandbox-password` or `test-pass`.
Rejected values produce an accessible toast and are not advanced or stored.
Set `PHISIM_SANDBOX_CAPTURE=false` for a telemetry-only demo.

Open the local address printed by Uvicorn. The safe default is `127.0.0.1:8000`.

To run the application without auto-reload:

```bash
uv run phisim
```

## Common workflows

### Operator Lab

1. Open `/lab`.
2. Choose a fictional scenario and target role.
3. Launch the local run.
4. Open the generated victim context in another tab.
5. Observe delivery, interaction, destination, and manual-end state in the Lab.
6. Open `/console` to inspect the event timeline and indicators.

### Victim experience

The primary victim routes are intentionally application-shaped:

- `/mail` — branded Gemail mailbox
- `/messages` — branded QuickChat conversation list
- `/v/{token}/mail` — mailbox for the active local run
- `/v/{token}/messages` — conversations for the active local run
- `/v/{token}/site/{scenario_id}` — product-specific target application
- `/v/{token}/qr/{scenario_id}` — local QR context and scan
- `/v/{token}/mfa/{scenario_id}/{step}` — bounded MFA prompt sequence

After a meaningful action, the participant reaches a product-specific destination. The destination remains active until the participant or operator explicitly ends the simulation.

### Compatibility routes

Older routes remain available for local demonstrations and integration coverage:

- `/scenario/{scenario_id}` — legacy website flow
- `/inbox` and `/sms` — legacy mailbox and messenger views
- `/qr/{scenario_id}` and `/mfa/{scenario_id}/{step}` — legacy QR and MFA flows

## Project surfaces

| Surface             | Route                                  | Purpose                                                                         |
| ------------------- | -------------------------------------- | ------------------------------------------------------------------------------- |
| Scenario Lab        | `/lab`                                 | Launch and observe bounded local runs                                           |
| Victim applications | `/mail`, `/messages`, `/v/{token}/...` | Fictional participant experiences                                               |
| Analyst Console     | `/console`                             | Safe event timeline, indicators, and session inspection                         |
| Training Reveal     | Product destination → `End simulation` | Debrief shown only after explicit completion                                    |
| API                 | `/api/*`                               | Scenario, session, event, Lab, analysis, and optional sandbox-capture contracts |
| Live events         | `/api/events/ws`                       | Local WebSocket event stream                                                    |

The Lab, victim applications, Console, and Reveal are separate presentation shells. They share contracts and safe infrastructure, not a single generic dashboard.

## Architecture

```text
Simulation
    ↓
Telemetry events
    ↓
Persistence ──→ Analysis / inspection
    ↓                    ↓
Local WebSocket  → Analyst Console
```

Important directories:

```text
src/phisim/
├── analysis/       deterministic indicator analysis
├── console/        analyst-facing integration
├── infra/          SQLite models and repositories
├── inspection/     timeline and explanation helpers
├── security/       fail-closed metadata guardrails
├── simulation/     local scenario channels and state
├── telemetry/      event API and WebSocket delivery
└── main.py         FastAPI composition root

web/
├── static/         local CSS and browser JavaScript
└── templates/      product, victim, Lab, Console, and Reveal templates

scenarios/          typed local scenario catalog
tests/              automated tests
docs/               project documentation
```

Simulation code emits safe events; it does not know how events are stored or displayed. Browser code consumes API/event contracts and does not access SQLAlchemy models directly.

Scenario-flow controls use bounded randomized client-side transition buffers. Payment and order confirmation receives the longest range; the global transition ceiling is `1800ms`. Lab, Console, inbox, messaging, and analytics surfaces do not use these buffers.

## Safety invariants

These are release-blocking constraints:

- The server binds to loopback by default.
- All organizations, users, messages, and domains are fictional.
- Normal telemetry never persists, logs, broadcasts, or returns submitted credential values.
- The opt-in synthetic sandbox capture is isolated from telemetry: non-secret demo values are stored locally, secret-like values receive salted digests, and exact secret display is limited to the active process-local session cache.
- Event metadata contains allowlisted, non-secret facts only.
- Email, SMS, QR targets, and attachment previews are local and inert.
- No SMTP, SMS gateway, cloud provider, external API, or outbound network call is required.
- Attachments are text/metadata previews only; they are never downloaded or executed.
- No endpoint executes shell commands, Python code, or arbitrary files.

See [`docs/SECURITY.md`](docs/SECURITY.md) for the complete boundary.

## Development commands

```bash
uv run dev          # start the development server
uv run test         # run the test suite
uv run lint         # run Ruff lint checks
uv run format       # format Python code
uv run typecheck    # run Pyright
uv run check        # lint, format check, typecheck, and tests
uv run clean        # remove local Python caches
```

Run one test file or test selection with pytest:

```bash
uv run pytest tests/simulation/test_ui_realism_flows.py
uv run pytest -k "destination or telemetry"
```

The current verification target is the full local path:

```text
Lab → delivery → victim application → interaction → destination
   → safe telemetry → analysis → Console → manual end → Reveal
```

## Documentation

Start with [`docs/README.md`](docs/README.md) for the documentation map.

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — boundaries and contracts
- [`docs/SECURITY.md`](docs/SECURITY.md) — safety and privacy rules
- [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) — setup and contribution workflow
- [`docs/CODE_STYLE.md`](docs/CODE_STYLE.md) — Python and design conventions
- [`docs/DECISIONS.md`](docs/DECISIONS.md) — architectural decisions
- [`docs/ai/UI_REALISM_AUDIT.md`](docs/ai/UI_REALISM_AUDIT.md) — UI boundaries and audit
- [`docs/ai/UI_REALISM_TEST_REPORT.md`](docs/ai/UI_REALISM_TEST_REPORT.md) — route verification evidence
- [`docs/ai/UI_REALISM_FINAL_REPORT.md`](docs/ai/UI_REALISM_FINAL_REPORT.md) — final UI status and limitations

## Contributing

Read [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) before making a change. Keep changes small, preserve the safety invariants, add focused tests, and run `uv run check` before opening a review.

## License and intended use

This project is intended for controlled education, demos, and defensive awareness training. Use it only on systems and accounts you are authorized to test. Do not adapt it for real credential collection, external delivery, or unauthorized targeting.
