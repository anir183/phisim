# PhiSim UI Realism Test Report

**Date:** 2026-09-25
**Branch:** `feature/team-1`
**Result:** PASS with documented browser limitation

## Scope

This report records route-level and automated verification for the UI realism
pass. The verification target is the complete local path:

```text
Lab → Scenario → Session → Delivery → Victim application → Interaction
→ Telemetry → Analysis → Console → Reveal
```

All checks used the local FastAPI application and an isolated SQLite test
engine. No real credentials, providers, domains, devices, or external network
services were used.

## Automated verification

Command:

```text
UV_PROJECT_ENVIRONMENT=/tmp/opencode/phisim-final-venv \
UV_CACHE_DIR=/tmp/opencode/phisim-final-uv-cache \
uv run check
```

Final result:

```text
120 files already formatted
0 errors, 0 warnings, 0 informations
187 passed, 1 existing Starlette/httpx deprecation warning
```

The warning is the existing test-client deprecation warning:

```text
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated;
install `httpx2` instead.
```

The UI realism route matrix is implemented in
`tests/simulation/test_ui_realism_flows.py` and covers the six requested
manual-verification surfaces.

## Manual route verification

The following walks were executed through the local `TestClient`, with delivery
timestamps moved to the deterministic due state. They exercise the same route
and template branches used by the application; they are not just static marker
checks.

| Flow | Route walk | Verified states and structure | Result |
|---|---|---|---|
| Gemail | `/v/{token}/mail` → message detail → message state POST → starred folder | Empty baseline, delivered row, unread state, search, detail, star/archive state, local link, attachment entry | PASS |
| QuickChat | `/v/{token}/messages` → conversation detail → message link | Empty baseline, delivered conversation, unread marker, last-message preview, search, contact header, bubbles, read-only composer | PASS |
| Amazaun | `/v/{token}/site/credential-shopping-001` → continue → checkout → finish → debrief | Marketplace header, order number, pending delivery, address confirmation, order timeline, completion reveal | PASS |
| CloudBox | `/v/{token}/site/credential-cloud-001` → continue → verification → finish → debrief | File sidebar, shared files, storage meter, activity, sharing action, verification state, completion reveal | PASS |
| QR | `/v/{token}/qr/qr-phish-001` → scan → local destination | Message context, local QR image, destination preview, scan transition, target application handoff | PASS |
| MFA | `/v/{token}/mfa/mfa-fatigue-001/1` → approve → prompt 2 | Device prompt, request scopes, location, request history, repeated prompt state, local response | PASS |

### Gemail evidence

- `web/templates/victim_mail.html` renders a folder rail, category tabs, dense
  message rows, search, unread state, and local message actions.
- `web/templates/victim_email.html` renders a message reader with sender,
  recipient, timestamp, link preview, attachment entry, and local link CTA.
- `POST /v/{token}/mail/{message_id}/state` persists only safe message IDs and
  action metadata (`star`, `archive`, `delete`, and restoration).
- Search and folder state are derived from the attack instance, so repeated
  deliveries remain separate.

### QuickChat evidence

- `web/templates/victim_messages.html` renders a conversation index, search,
  unread markers, and a selected-conversation empty state.
- `web/templates/victim_message.html` renders contact context, message history,
  a last-message preview, a local link bubble, and a disabled read-only composer.
- The disabled composer is intentional: it preserves believable interaction
  affordances without accepting or persisting free-form user content.

### Amazaun evidence

- `web/templates/apps/amazaun/home.html` is an order page, not a generic
  dashboard: navigation/search, order identity, delivery timeline, pending
  status, and contextual address action.
- `web/templates/apps/amazaun/checkout.html` is a distinct confirmation step.
- The final action transitions to the standalone training reveal, not a generic
  processing screen.

### CloudBox evidence

- `web/templates/apps/cloudbox/home.html` is a file workspace with My Files,
  Recent, Starred, Shared, Trash, storage, activity, and shared-file context.
- `web/templates/apps/cloudbox/verify.html` is a separate shared-file
  verification state.
- No file is uploaded, downloaded, opened, or executed.

### QR evidence

- `web/templates/apps/qr/scan.html` presents a message/poster context and a
  destination preview before the simulated scan.
- The QR image is generated locally and points to a local route only.
- The scan transition emits the existing `qr_scan_simulated` telemetry event.

### MFA evidence

- `web/templates/apps/mfa/prompt.html` presents requested scopes, device,
  location, expiry, and a request history.
- Primary and compatibility routes use the same product-specific prompt
  composition while retaining their existing route contracts.
- Repeated prompt and terminal response events remain covered by the existing
  MFA tests.

## Additional application checks

The following route checks also passed:

- All website target families render distinct application classes and fictional
  hosts: UniSecure, Amazaun, CloudBox, PayMate, UniSecure Support, MAKExam, and
  TechnoSphere.
- Legacy `/inbox` and `/sms` compatibility routes use the improved mailbox and
  messenger structures rather than the old generic fake-app layout.
- Attachment previews render an inert document viewer and retain the explicit
  no-download/no-execute boundary.
- Scenario Lab renders a distinct operator control plane with run metrics,
  delivery state, catalogue controls, and the Lab → Session → Delivery →
  Telemetry → Console path.
- Analyst Console retains safe DOM APIs (`textContent`/`replaceChildren`) and
  renders a distinct evidence-oriented workspace.
- Training reveal uses `reveal_base.html`, not the victim application shell.
- Empty, delivered, unread, read, pending, verification-required, success, and
  completion states are represented in the relevant route families.

## Regression follow-up

`tests/simulation/test_ui_regressions.py` additionally verifies:

- completed and abandoned email/SMS lists remain visible and their details
  render read-only; state-changing actions return `410 Gone`;
- account verification progress is outside the alert content;
- TechnoSphere has separated navigation and course-access structure;
- the Lab and analyst Console render with the light workspace class;
- the Console keeps its evidence layout while using the light palette;
- Gemail and MFA contrast/hover selectors are present;
- QuickChat shows the last message, removes typing indicators, and clears its
  unread marker after opening.

## Safety verification

The test suite continues to enforce the following boundaries:

- submitted values are not persisted, logged, broadcast, or returned;
- local delivery state and attack IDs remain the source of truth;
- message and conversation links resolve only to local routes;
- attachments are inert text/metadata previews;
- QR destinations are local;
- MFA responses emit safe metadata only;
- no external asset or network dependency was added;
- operator, victim, analyst, and reveal shells are separate templates/styles.

## Manual browser limitation

A connected desktop browser was not available in this session. The browser
integration reported:

```text
[browser.disconnected] No desktop browser is connected to this session.
```

Therefore this report does not claim screenshot or browser accessibility-tree
inspection. The route-level walks above are the available manual verification
evidence. A future browser pass should capture desktop/mobile screenshots for
Gemail, QuickChat, Amazaun, CloudBox, QR, and MFA and inspect keyboard focus,
labels, landmarks, and responsive reflow.

## Conclusion

The application-specific UI pass is functionally verified across the requested
flows. The remaining verification gap is visual screenshot/accessibility
inspection in a connected desktop browser, not a failing route or safety test.
