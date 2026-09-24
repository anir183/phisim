# Team 3 --- Analysis / Inspection / Security

## Owned paths

``` text
src/phisim/analysis/
src/phisim/inspection/
src/phisim/security/
tests/analysis/
tests/inspection/
tests/security/
```

## Mission

Turn simulation telemetry into explainable defensive observations and
enforce safety constraints.

## Phase 0

-   [x] define indicator structure
-   [x] define indicator codes
-   [x] implement deterministic rules
-   [x] define evidence/explanation format
-   [x] create analysis fixtures
-   [x] define secret-stripping/security checks

Initial indicators:

``` text
credential_request
urgent_language
unexpected_link
domain_mismatch
authority_impersonation
suspicious_attachment
unusual_mfa_request
```

## Phase 1

-   [ ] scenario-aware indicator rules
-   [ ] session-level aggregation
-   [ ] inspection/timeline explanation
-   [ ] console-ready analysis results

## Rules

Analysis should not own UI rendering.

Inspection should explain analysis results rather than duplicate their
detection logic.

Security helpers should enforce concrete constraints, not become a
generic policy engine.

## Output principle

Prefer:

``` text
indicator code
evidence
explanation
context
```

over an unexplained numeric score.
