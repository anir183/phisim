# PhiSim Code Style

## 1. General rule

Prefer code that a teammate can understand after one reading.

Use:

-   small functions
-   explicit names
-   typed inputs/outputs
-   direct control flow
-   standard-library features where sufficient
-   existing project dependencies before adding new ones

Avoid:

-   clever metaprogramming
-   speculative abstractions
-   framework-heavy patterns for small features
-   global mutable state unless it is genuinely application
    infrastructure

------------------------------------------------------------------------

## 2. Modularity

A module should have one obvious responsibility.

Good:

``` text
telemetry/service.py
telemetry/routes.py
telemetry/schemas.py
```

Less useful:

``` text
helpers.py
common.py
misc.py
stuff.py
```

Do not split a 30-line piece of logic into five interfaces merely
because it can be done.

------------------------------------------------------------------------

## 3. Deduplication

The project follows:

> Deduplicate stable concepts, not every repeated line.

Acceptable repetition:

-   two small repository queries that are easier to read independently
-   similar route handlers with different semantics
-   scenario-specific presentation details

Good candidates for reuse:

-   event creation
-   session lookup
-   safe event emission
-   common scenario metadata
-   common template layout
-   indicator construction

------------------------------------------------------------------------

## 4. Interfaces

Do not introduce an abstract base class or protocol unless at least one
of these is true:

1.  there are multiple concrete implementations;
2.  testing genuinely benefits from substitution;
3.  an external boundary requires it;
4.  the interface prevents a real dependency cycle.

One implementation does not automatically justify an interface.

------------------------------------------------------------------------

## 5. Type hints

Use type hints on public functions, methods, service boundaries, and
model attributes.

Prefer modern Python 3.14 syntax:

``` python
str | None
list[Event]
dict[str, Any]
```

Do not add annotations solely to satisfy a type checker when they make
the code less readable.

------------------------------------------------------------------------

## 6. Pydantic

Use Pydantic schemas at HTTP/application boundaries.

Schemas should describe contracts.

Do not pass raw request dictionaries deep into the application.

------------------------------------------------------------------------

## 7. SQLAlchemy

Keep database concerns inside `infra/sqlite`.

Routes should not contain SQLAlchemy queries.

Services should use repositories rather than constructing arbitrary SQL
queries.

------------------------------------------------------------------------

## 8. FastAPI

Keep routes thin:

``` text
parse/validate request
    -> call service
    -> map result to response
```

Do not put business logic into route functions.

------------------------------------------------------------------------

## 9. Errors

Raise domain/application exceptions where useful.

Translate them to HTTP errors at the route boundary.

Do not expose raw database errors to users.

For expected conflicts, return deterministic HTTP behavior.

------------------------------------------------------------------------

## 10. Async

Use async where it corresponds to actual I/O or framework boundaries.

Do not make CPU-bound functions async merely for consistency.

Do not block the event loop with expensive work.

------------------------------------------------------------------------

## 11. Naming

Use descriptive names.

Prefer:

``` python
record_event()
get_session_events()
credential_submission_attempted
```

over:

``` python
do_event()
get_data()
submit
```

Event types should be stable and lowercase with underscores.

------------------------------------------------------------------------

## 12. Templates and browser code

Never assume browser-visible event data is trusted.

Avoid:

``` javascript
element.innerHTML = userControlledValue;
```

Prefer:

``` javascript
element.textContent = userControlledValue;
```

Keep large JavaScript/CSS blocks out of templates once a feature becomes
non-trivial.

------------------------------------------------------------------------

## 13. Tests

Test behavior, not implementation details.

Good:

``` text
POST /api/events -> 201
duplicate event_id -> 409
credential submission -> event without password
indicator rule -> expected indicator
```

Avoid tests that merely assert private helper call counts unless those
calls are the actual contract.

------------------------------------------------------------------------

## 14. Ruff / formatting

The project uses Ruff for linting and formatting.

Run:

``` text
uv run lint
uv run format
uv run typecheck
uv run test
uv run check
```

Do not manually reformat unrelated files.

------------------------------------------------------------------------

## 15. Comments

Comment **why**, not what.

Bad:

``` python
# Add one to count
count += 1
```

Good:

``` python
# Keep the browser-facing identifier stable so duplicate submissions remain idempotent.
```

Remove comments that become inaccurate.

------------------------------------------------------------------------

## 16. Dependencies

Before adding a dependency:

1.  check whether the standard library already solves it;
2.  check whether an existing dependency already provides the
    capability;
3.  consider maintenance and cross-platform behavior;
4.  add the smallest dependency that solves the actual requirement.

Update the lockfile through `uv`, not by editing `uv.lock` manually.

------------------------------------------------------------------------

## 17. Simplicity rule

When two designs are functionally equivalent, prefer the one with:

-   fewer files
-   fewer abstractions
-   fewer dependencies
-   fewer global states
-   clearer ownership
-   easier tests

Do not optimize for theoretical scale before the classroom project needs
it.
