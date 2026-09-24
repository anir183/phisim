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

-   [x] retain current live event view
-   [x] safe DOM rendering
-   [x] session/scenario summary
-   [x] event timeline
-   [x] event detail
-   [x] basic filtering
-   [x] reconnect/error handling for WebSocket

## P1

-   [x] indicator panel
-   [x] scenario detail
-   [x] session detail
-   [x] interaction timeline
-   [x] clearer analysis evidence

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

## Staging implementation

There was no separate Team 4 branch to merge. The staging implementation in
`web/templates/console.html` renders all dynamic values with DOM text APIs,
loads the latest or a selected Session through REST, displays Event/Scenario/
Session context and indicators, and reconnects the WebSocket with bounded
backoff. Malformed frames are ignored without interrupting the console.
