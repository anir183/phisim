# Team 2 --- Simulation Channels

## Owned paths

``` text
src/phisim/simulation/
scenarios/
web/templates/simulation/
web/static/simulation/
tests/simulation/
```

## Mission

Build safe, fictional phishing experiences on top of the shared
telemetry/session contracts.

## P0

### Fake credential site

-   [ ] scenario metadata
-   [ ] fake login page
-   [ ] safe submission handling
-   [ ] `credential_submission_attempted`
-   [ ] educational outcome page
-   [ ] test that submitted password is not persisted/emitted

### Email

-   [ ] simulated message representation
-   [ ] message-open interaction
-   [ ] link-click interaction
-   [ ] optional harmless attachment interaction
-   [ ] tests

### SMS

-   [ ] simulated conversation/message
-   [ ] link-click interaction
-   [ ] tests

## P1

-   [ ] spear phishing
-   [ ] whaling
-   [ ] clone phishing
-   [ ] urgency
-   [ ] tech support
-   [ ] QR/quishing
-   [ ] attachment
-   [ ] link spoofing
-   [ ] BEC
-   [ ] MFA fatigue

## Contract expectations

Emit telemetry through the public telemetry boundary.

Do not:

-   import SQLAlchemy models directly
-   write to SQLite directly
-   modify the analyst console
-   store passwords
-   send real email/SMS

## Design goal

Scenario-specific content should be data/template-driven where useful.

Do not build a new framework for every scenario.
