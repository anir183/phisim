# AI Work Area

This directory contains focused planning, interface, audit, and verification notes for the implementation workstreams.

Canonical project policy remains in [`docs/*.md`](../README.md). Application behavior is always verified against the source tree and tests.

## Files

| File                         | Purpose                                                 |
| ---------------------------- | ------------------------------------------------------- |
| `team-1-backend.md`          | Backend, persistence, lifecycle, and platform contracts |
| `team-2-simulation.md`       | Local simulation channels and victim experiences        |
| `team-3-analysis.md`         | Analysis, inspection, and security guardrails           |
| `team-4-console.md`          | Analyst Console contracts and presentation rules        |
| `integration.md`             | Cross-team contracts and integration state              |
| `ai-task-template.md`        | Reusable task and handoff format                        |
| `UI_REALISM_AUDIT.md`        | Application-boundary and UI realism audit               |
| `UI_REALISM_TEST_REPORT.md`  | Route-level and automated verification evidence         |
| `UI_REALISM_FINAL_REPORT.md` | Final UI status, limitations, and acceptance summary    |

`REALISM_AUDIT.md` and `REBUILD_AUDIT.md` are retained as historical implementation records. They are not the current status source.

## Working rules

- Read [`docs/AI.md`](../AI.md) before changing an AI workstream file.
- Inspect the source tree and existing tests before planning a change.
- Keep these files focused; do not duplicate the full architecture document.
- Prefer updating the owning workstream note over creating another status file.
- Remove stale handoff notes when their contracts are represented in canonical docs.
- Keep generated reports and temporary evidence out of the repository unless they are explicitly requested.

## Task sequence

1. Read the canonical project documentation.
2. Read this file and the relevant workstream note.
3. Inspect the implementation and tests.
4. Make the smallest coherent change.
5. Run focused tests, then `uv run check`.
6. Update the relevant note with the contract or verification result.
