# Git Manners

The primary Git goal is to make four people work in parallel without
repeatedly resolving the same conflicts.

## 1. Branch model

Use:

```text
main   = stable/reviewed state
dev    = active integration branch
feature/* = individual work
```

Each member works from a feature branch.

Examples:

```text
feature/backend-sessions
feature/simulation-p0
feature/analysis-indicators
feature/console-timeline
```

Do not commit directly to `main`.

---

## 2. Ownership

Default ownership:

Area Owner

---

`src/phisim/infra/` Team 1
`src/phisim/telemetry/` Team 1
`src/phisim/utils/` Team 1
`src/phisim/simulation/` Team 2
`scenarios/` Team 2
simulation templates/static Team 2
`src/phisim/analysis/` Team 3
`src/phisim/inspection/` Team 3
`src/phisim/security/` Team 3
`src/phisim/console/` Team 4
console templates/static Team 4
`tests/` owner of the feature being tested

Shared root files require extra care:

```text
pyproject.toml
uv.lock
src/phisim/main.py
```

Only change these when necessary.

---

## 3. One task, one branch

A branch should represent one coherent change.

Bad:

```text
feature/email
+ email
+ database refactor
+ console redesign
+ Ruff cleanup
```

Good:

```text
feature/email
```

containing the email simulation and its tests.

---

## 4. Before starting

Update your branch:

```bash
git fetch origin
git rebase origin/dev
```

Then verify:

```bash
uv run check
```

Do not start substantial work on a stale branch.

---

## 5. During work

Commit small coherent units.

Good commit sequence:

```text
feat(simulation): add scenario metadata
feat(simulation): add fake login page
test(simulation): cover credential submission
```

Avoid:

```text
final changes
stuff
updates
fix
```

---

## 6. Do not perform drive-by formatting

If a file is not part of your task:

- do not reformat it;
- do not rename unrelated variables;
- do not reorder imports merely because you noticed them;
- do not "clean up" neighboring code.

This is one of the easiest ways to create merge conflicts.

---

## 7. Shared contract changes

If a feature requires changing a shared schema:

1.  identify every consumer;
2.  document the proposed change in the relevant `docs/ai/*.md`;
3.  notify the affected team;
4.  make the smallest compatible change;
5.  update tests;
6.  integrate the contract change before large dependent work.

Prefer additive changes when possible.

---

## 8. Root-file changes

Avoid simultaneous edits to:

```text
pyproject.toml
src/phisim/main.py
docs/README.md
```

If two branches need the same root file, coordinate who changes it
first.

---

## 9. Rebase before integration

Before opening a PR:

```bash
git fetch origin
git rebase origin/dev
uv run check
```

Resolve conflicts locally.

Never resolve a conflict by blindly choosing "ours" or "theirs".

Understand both sides first.

---

## 10. Conflict-resolution order

When a conflict occurs:

1.  identify why both changes touch the same lines;
2.  preserve both behaviors if both are required;
3.  move shared logic into an appropriate owner module if that reduces
    coupling;
4.  run focused tests;
5.  run the complete check;
6.  commit the conflict resolution separately if useful.

---

## 11. Generated and environment files

Do not commit:

```text
.env
data/phisim.db
.venv/
__pycache__/
.pytest_cache/
.ruff_cache/
.pyright/
build/
dist/
```

`uv.lock` is committed and should only change as a consequence of
dependency management.

---

## 12. Documentation ownership

Canonical project documentation lives in:

```text
docs/*.md
```

Human-maintained docs are not scratchpads.

AI planning/interface material belongs in:

```text
docs/ai/*.md
```

AI agents must not modify canonical `docs/*.md` files unless a human
explicitly requests a documentation edit and the agent is operating
under that request.

---

## 13. Pull requests

A PR should state:

- what changed
- why
- files/areas affected
- tests run
- contract changes
- security implications
- any follow-up work

Keep PRs small enough to review.

---

## 14. Integration order

When multiple branches are ready:

1.  contracts/platform
2.  simulation/backend consumers
3.  analysis
4.  console integration
5.  polish

This is not a quality ranking. It is a dependency order.

---

## 15. Emergency rule

If you need a file owned by another team:

Do not silently modify it.

Ask the owner for:

- a contract,
- a small helper/API,
- or a coordinated change.

This keeps ownership useful instead of turning the project into a
shared-file bottleneck.
