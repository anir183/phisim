# Cross-Team Integration

## Current dependency graph

``` text
Team 1 backend/platform
       |
       +----> Team 2 simulation
       |
       +----> Team 3 analysis
       |
       +----> Team 4 console

Team 2 simulation
       |
       v
Team 1 telemetry
       |
       v
Team 3 analysis
       |
       v
Team 4 console
```

This is a dependency graph, not a quality ranking.

## Integration order

1.  backend/event contracts
2.  scenario/session contracts
3.  fake-site vertical slice
4.  analysis integration
5.  console integration
6.  email
7.  SMS
8.  remaining scenarios

Email/SMS may be developed in parallel after the basic telemetry
contract is stable.

## Shared contract checklist

Before changing a shared contract:

-   [ ] identify all consumers
-   [ ] write the intended change here
-   [ ] make the smallest compatible change
-   [ ] add/update tests
-   [ ] notify affected team
-   [ ] avoid simultaneous edits to the same root files

## P0 integration scenario

``` text
start session
    |
open fake site
    |
submit fake credentials
    |
emit credential_submission_attempted
    |
persist event
    |
run analysis
    |
broadcast event
    |
console displays event + indicator
```

## Current known cleanup

The existing event tests still send a `timestamp` field in create
requests even though timestamp is server-generated. Remove that stale
input from the tests as part of backend contract cleanup.

## Integration rule

If an implementation can wait for another team's stable contract, do not
bypass the contract by importing that team's internals.

## First 2--3 hour team run

The first shared session should optimize for a working vertical slice,
not feature count.

### Parallel start

``` text
Team 1: Event + Scenario + Session contracts
Team 2: Fake credential site
Team 3: Indicator fixtures/rules + secret-safety test
Team 4: Console event/session view
```

### Integration checkpoint

At the end of the first run:

``` text
fake site
  -> event
  -> persistence
  -> analysis
  -> WebSocket
  -> console
```

Do not start email/SMS integration until this path works.

### Next run

Use the same primitives to add:

``` text
fake email inbox -> fake email -> local link
fake SMS thread  -> fake message -> local link
```

No external delivery APIs are involved.

## Integration checklist

-   [ ] scenario can be identified without hardcoded UI-only state
-   [ ] session is created/reused correctly
-   [ ] event has stable event_id
-   [ ] timestamp is server-generated
-   [x] submitted password never appears in event metadata
-   [ ] duplicate events are handled deterministically
-   [x] analysis consumes events rather than database internals
-   [ ] console consumes API/WebSocket contracts rather than SQLAlchemy
-   [ ] all links remain local
-   [ ] no external delivery provider is configured
