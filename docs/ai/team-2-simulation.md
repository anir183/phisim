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

-   [x] scenario metadata
-   [x] fake login page
-   [x] safe submission handling
-   [x] `credential_submission_attempted`
-   [x] educational outcome page
-   [x] test that submitted password is not persisted/emitted

Scenario `credential-basic-001` is implemented in
`phisim/simulation/catalog.py`, `routes.py`, and `web/templates/simulation/`.
See `docs/ai/integration.md` for contract notes.

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

## P0 channel implementation details

### Email

Implement a **local fake mailbox** using the existing FastAPI + Jinja2
stack.

Do not add an email delivery provider.

The P0 path is:

``` text
local browser
  -> fake inbox
  -> fake email
  -> local link
  -> scenario
  -> telemetry
```

Useful event types:

``` text
message_opened
link_clicked
attachment_opened
```

An attachment must be inert. A suspicious filename can be displayed
without creating an executable payload.

Python's standard-library `email` module is optional for later
educational work involving MIME/header representation; it is not
required for P0.

### SMS

Implement a **local fake messaging conversation** using FastAPI +
Jinja2.

Do not add an SMS provider.

The P0 path is:

``` text
local browser
  -> fake conversation
  -> local link
  -> scenario
  -> telemetry
```

Useful event types:

``` text
message_opened
link_clicked
```

Use fictional sender identities. Do not model a real phone-number
campaign.

### Dependency rule

The P0 email and SMS features require **no additional third-party
package**.

Do not add:

``` text
SMTP libraries/services
Twilio
Vonage
AWS SNS
Firebase messaging
Gmail API
Microsoft Graph
SendGrid
Mailgun
Resend
```

unless a future human-approved requirement explicitly changes the
project's safety boundary.
