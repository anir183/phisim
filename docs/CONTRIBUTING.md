# Contributing to PhiSim

This guide is intended for both human contributors and AI-assisted
development.

It assumes a fresh Windows, macOS, or Linux machine.

## 1. Required tools

The project uses:

- Git
- Python 3.14
- `uv`
- optionally `mise`
- a code editor such as VS Code, Neovim, or another editor

The project itself does not require Docker.

---

## 2. Install Git

### Windows

Install Git for Windows from the official Git distribution.

After installation:

```powershell
git --version
```

### macOS

Install Xcode Command Line Tools or Git:

```bash
git --version
```

### Linux

Use your distribution's package manager.

Verify:

```bash
git --version
```

---

## 3. Install Python and uv

### Preferred: mise

The repository contains `mise.toml` with the intended Python and uv
versions.

After installing mise:

```bash
mise install
```

Then:

```bash
python --version
uv --version
```

### Alternative: install directly

If mise is unavailable, install Python 3.14 and uv using their
platform-supported installers.

Then verify:

```bash
python --version
uv --version
```

The exact installer mechanism may differ by operating system.

---

## 4. Clone the repository

```bash
git clone <repository-url>
cd phisim
```

Switch to the development branch if required:

```bash
git switch dev
```

---

## 5. Create the environment

The project is managed by `uv`.

Run:

```bash
uv sync
```

This creates the project environment and installs runtime/development
dependencies from the lockfile.

Do not manually create a `.venv` with `python -m venv` unless there is a
specific reason.

---

## 6. Environment configuration

Copy the example environment file.

### macOS/Linux

```bash
cp .env.example .env
```

### PowerShell

```powershell
Copy-Item .env.example .env
```

Keep `.env` local.

Do not commit it.

The important settings are:

```text
PHISIM_ENV
PHISIM_HOST
PHISIM_PORT
PHISIM_DB_URL
```

The safe default host is loopback:

```text
127.0.0.1
```

Do not change it to `0.0.0.0` for normal development.

---

## 7. Start PhiSim

Preferred development command:

```bash
uv run dev
```

The configured FastAPI entry point is:

```text
phisim.main:app
```

Open the local development address printed by Uvicorn.

Do not expose the development server to the public internet.

---

## 8. Useful commands

```bash
uv run dev
uv run test
uv run lint
uv run format
uv run typecheck
uv run check
uv run clean
```

`check` is the normal pre-PR validation command.

---

## 9. Running one test

Use pytest through uv:

```bash
uv run pytest tests/telemetry/test_routes.py
```

Or a specific test:

```bash
uv run pytest tests/telemetry/test_routes.py -k duplicate
```

---

## 10. VS Code

Open the repository root.

Recommended extensions:

- Python
- Pylance or equivalent Python language support
- Ruff
- Git tooling

The editor should use the project's `.venv` interpreter created by `uv`.

Do not add editor-specific generated configuration to the repository
unless the team agrees that it is useful for everyone.

---

## 11. Windows notes

Prefer PowerShell or Windows Terminal.

The project commands themselves are intentionally platform-neutral:

```powershell
uv run dev
uv run check
```

Avoid shell scripts that assume Bash unless there is a clear need.

Python code should use `pathlib`, not manually constructed `/` paths.

---

## 12. macOS/Linux notes

The same `uv run ...` commands apply.

Do not assume GNU-specific shell tools are available in application code
or contributor workflows.

---

## 13. Development workflow

Create a branch:

```bash
git switch dev
git pull --rebase
git switch -c feature/my-change
```

Before coding:

```bash
uv run check
```

After coding:

```bash
uv run check
```

Commit only related changes.

---

## 14. AI-assisted development

AI is allowed and expected as a development aid.

The AI must:

- read `docs/AI.md`
- read the relevant `docs/ai/*.md`
- inspect the actual source before changing it
- respect subsystem ownership
- keep changes small
- run tests
- avoid unrelated refactors
- avoid editing canonical `docs/*.md`

See `docs/AI.md`.

---

## 15. Safe simulation development

Never turn a classroom simulation into a real phishing tool.

Do not add:

- real recipient lists
- real SMTP credentials
- SMS gateway credentials
- password databases
- executable attachments
- credential replay
- public campaign endpoints
- arbitrary shell execution
- arbitrary file upload/execution
- real organization identities

Use fictional domains and identities.

---

## 16. Database development

The default database is local SQLite.

Do not commit:

```text
data/phisim.db
```

If database models change:

1.  update the model;
2.  update repository/service behavior;
3.  update tests;
4.  document the contract change;
5.  consider whether a migration strategy is needed before
    production-like persistence is introduced.

Do not manually edit the SQLite file as a development feature.

---

## 17. Adding a feature

A feature should normally follow:

```text
contract
  -> backend/application behavior
  -> simulation/UI behavior
  -> analysis
  -> tests
```

The actual order depends on ownership and dependencies.

Do not start by modifying a shared root file if the feature can be
isolated.

---

## 18. Pull request checklist

Before requesting review:

- [ ] Scope is focused.
- [ ] Correct team-owned paths were used.
- [ ] No `.env` or local DB was committed.
- [ ] No unrelated formatting was introduced.
- [ ] Tests were added/updated.
- [ ] `uv run check` passes.
- [ ] Contract changes are explicitly documented.
- [ ] Security boundary remains intact.
- [ ] No real delivery mechanism was added.

---

## 19. Short collaborative development sessions

For a 2--3 hour team session, use this rhythm.

### 0--15 minutes

- pull/rebase from `dev`
- read the relevant `docs/ai/*.md`
- agree on contracts
- confirm file ownership

### 15--90 minutes

Work in parallel on owned files.

Avoid shared root files unless required.

### 90--120 minutes

Integrate the smallest working path.

Run focused tests.

### 120--180 minutes, if available

- fix integration issues
- run `uv run check`
- update the relevant `docs/ai/*.md`
- commit coherent changes
- prepare the next handoff

Do not spend the entire session on architecture discussion.

The first short-session milestone is the fake-site vertical slice. The
next is email + SMS using the same primitives.
