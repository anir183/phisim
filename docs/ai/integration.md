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
