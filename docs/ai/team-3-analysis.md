# Team 3 --- Analysis / Inspection / Security

## Owned paths

```text
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

- [x] define indicator structure
- [x] define indicator codes
- [x] implement deterministic rules
- [x] define evidence/explanation format
- [x] create analysis fixtures
- [x] define fail-closed secret-safety checks

Initial and catalog-aligned indicators:

```text
credential_request
urgent_language
unexpected_link
domain_mismatch
authority_impersonation
suspicious_attachment
unusual_mfa_request
personalization
incident_fear
tech_support
invoice_fraud
request_confirmation
out_of_band
spoiled_links
attachment_lure
mfa_fatigue
```

## Phase 1

- [x] scenario-aware indicator rules
- [x] session-level aggregation
- [x] inspection/timeline explanation
- [x] console-ready analysis results

## Integrated contract

Analysis consumes validated `EventResponse` values. The WebSocket boundary
attaches deterministic indicators to each live Event, and
`GET /api/analysis/sessions/{session_id}` (also available as
`GET /api/sessions/{session_id}/analysis`) returns deduplicated indicators
plus a UTC `Z` timeline for reconnecting clients.

Simulation evidence uses non-secret fields such as `subject`, `content`,
`channel`, link targets, attachment names, and explicit catalog flags. The
security guardrail rejects raw or nested credential keys; it never silently
strips them. The Team 1 credential allowlist remains authoritative.

## Output principle

Prefer:

```text
indicator code
evidence
explanation
context
```

over an unexplained numeric score.
