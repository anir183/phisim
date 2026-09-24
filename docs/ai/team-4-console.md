# Team 4 --- Analyst Console

## Owned paths

``` text
src/phisim/console/
web/templates/console/
web/static/console/
tests/console/
```

## Mission

Build the analyst-facing experience without coupling it to database
internals.

## P0

-   [ ] retain current live event view
-   [ ] safe DOM rendering
-   [ ] session/scenario summary
-   [ ] event timeline
-   [ ] event detail
-   [ ] basic filtering
-   [ ] reconnect/error handling for WebSocket

## P1

-   [ ] indicator panel
-   [ ] scenario detail
-   [ ] session detail
-   [ ] interaction timeline
-   [ ] clearer analysis evidence

## Contracts consumed

Backend:

``` text
scenario API
session API
event API
WebSocket event stream
```

Analysis:

``` text
indicator code
evidence
explanation
context
```

## Rules

Do not:

-   query SQLite from browser code
-   import SQLAlchemy models
-   add business logic to templates
-   use unsafe `innerHTML` for event values

Keep browser-facing code resilient when a field is missing or a backend
event arrives unexpectedly.
