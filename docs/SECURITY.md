# PhiSim Security and Safety Boundary

PhiSim is a phishing **simulation** and security-awareness laboratory.

Its purpose is to demonstrate recognizable phishing patterns and
defensive telemetry without enabling real phishing campaigns.

## 1. Safe defaults

The application must default to:

``` text
host = 127.0.0.1
```

The normal deployment is a local machine/browser.

Do not make public binding the default.

------------------------------------------------------------------------

## 2. Fictional content

Use:

-   fictional universities
-   fictional companies
-   fictional users
-   fictional domains
-   fictional messages

Do not impersonate real organizations for the classroom demonstration.

------------------------------------------------------------------------

## 3. Credentials

A fake login page may ask for a username and password to demonstrate the
interaction.

The system must not:

-   store the password
-   log the password
-   broadcast the password
-   include the password in an exception
-   send the password to another service
-   allow password replay

The safe event is:

``` text
credential_submission_attempted
```

with metadata such as:

``` text
field_presence
scenario_id
interaction_result
```

but never the secret itself.

------------------------------------------------------------------------

## 4. Email

Email phishing is simulated.

Do not add:

-   SMTP credentials
-   real recipients
-   bulk sending
-   external delivery
-   mail-server automation

Represent messages inside PhiSim or as local simulation artifacts.

------------------------------------------------------------------------

## 5. SMS

SMS phishing is simulated.

Do not add:

-   carrier APIs
-   phone-number lists
-   SMS credentials
-   external SMS sending

------------------------------------------------------------------------

## 6. Attachments

Attachment phishing should use inert educational artifacts.

Do not create executable attachments or code that launches payloads.

Examples can show a suspicious filename as text or use a harmless
document.

------------------------------------------------------------------------

## 7. QR phishing

QR codes may point to a local fictional simulation URL.

They must not point to a real credential-collection service or external
campaign.

------------------------------------------------------------------------

## 8. MFA fatigue

MFA fatigue is simulated entirely inside PhiSim.

Repeated prompts should be generated as UI/events.

No real MFA provider should be contacted.

------------------------------------------------------------------------

## 9. Network egress

The application should not require external network access.

New integrations that introduce network egress require explicit design
review.

------------------------------------------------------------------------

## 10. File and process safety

Do not expose HTTP endpoints that execute:

-   shell commands
-   Python code
-   arbitrary files
-   uploaded executables

Do not add server-side "utility" endpoints that can become arbitrary
execution primitives.

------------------------------------------------------------------------

## 11. Telemetry privacy

Telemetry should record simulation/security events, not unnecessary
personal data.

Prefer:

``` text
scenario_id
session_id
event_type
timestamp
safe metadata
```

over raw message contents or secrets.

------------------------------------------------------------------------

## 12. Security review trigger

Stop and review the design if a feature needs:

-   external network delivery
-   real credentials
-   real user targets
-   arbitrary file execution
-   process execution
-   persistent secrets
-   public exposure
-   real organization branding

The educational requirement should be solved with a safer simulation
mechanism whenever possible.

------------------------------------------------------------------------

## 13. Email/SMS implementation boundary

The local simulation UI is deliberately the only P0 "delivery"
mechanism.

### Email

``` text
Fake inbox -> fake message -> local interaction
```

There is no SMTP connection and no external email API.

### SMS

``` text
Fake conversation -> fake message -> local interaction
```

There is no carrier connection and no external SMS API.

This means a fresh PhiSim checkout does not need email/SMS credentials
and does not need outbound network access to demonstrate either feature.
