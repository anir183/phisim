# PhiSim UI Realism Final Report

**Date:** 2026-09-25
**Branch:** `feature/team-1`
**Delivery status:** Implemented and locally verified; connected-browser visual review pending

## Executive summary

PhiSim now presents its local training system as a set of distinct simulated
applications rather than one color-reskinned dashboard. Shared simulation
infrastructure remains centralized, while the user-facing information
architecture is selected by application type and scenario.

The pass covers:

- Gemail mailbox, folders/search, message reader, local message actions, and
  inert attachment previews;
- QuickChat conversation list, search, contact view, last-message previews,
  unread state, link bubble, and read-only composer;
- Amazaun order detail, delivery timeline, address confirmation, and checkout;
- CloudBox file browser, shared files, storage/activity context, and sharing
  verification;
- fictional university student services, MAKExam registration, and TechnoSphere
  course workspace;
- UniSecure Support case management, PayMate invoice review, NimbusID MFA
  approval, and QR destination preview;
- a distinct operator Lab, analyst Console, and training Reveal.

The final automated check passes with **187 tests**. One existing Starlette/
httpx test-client deprecation warning remains.

## Design architecture

### Shared infrastructure

The following remain shared intentionally:

- local sessions, attack instances, delivery timing, and lifecycle state;
- victim token/context management;
- safe event emission, persistence, WebSocket updates, analysis, and Console
  APIs;
- credential-safety validation and non-persistence guarantees;
- completion and explicit end-simulation controls;
- local-only asset and network-egress policy;
- baseline accessibility primitives and fictional safety framing.

### Application-specific presentation

The following are now selected by application/scenario rather than rendered
through one universal landing funnel:

- `web/templates/victim_mail.html` and `victim_email.html` — Gemail;
- `web/templates/victim_messages.html` and `victim_message.html` — QuickChat;
- `web/templates/apps/amazaun/` — order and checkout;
- `web/templates/apps/cloudbox/` — files and sharing;
- `web/templates/apps/university/` — student services, exams, and courses;
- `web/templates/apps/support/` — service desk and case verification;
- `web/templates/apps/payment/` — invoice and payment review;
- `web/templates/apps/mfa/` — NimbusID device prompts;
- `web/templates/apps/qr/` — message/poster and destination scan flow;
- `web/templates/lab.html` — operator run control plane;
- `web/templates/console.html` — analyst evidence plane;
- `web/templates/reveal_base.html` and `victim_reveal.html` — training debrief.

The intermediate `sites/landing.html` and `sites/verification.html` remain as
fallbacks for generic/unknown website targets, but all catalogued target
families now route to independent application compositions.

## Route and workflow results

| Area | Result |
|---|---|
| Lab → launch | Operator can filter the catalogue, launch a bounded run, and see active/recent state. |
| Session → delivery | Delivery remains deterministic and instance-scoped; repeated email/SMS deliveries remain separate. |
| Gemail | Delivered messages appear in a realistic mailbox; read/search/star/archive state is derived from the attack instance. |
| QuickChat | Delivered conversations appear in a split-pane messenger; unread/search/detail states are local and deterministic. |
| Amazaun | Context begins in an order page and advances through delivery confirmation and checkout. |
| CloudBox | Context begins in a file workspace and advances through shared-file verification. |
| University services | Student dashboard, exam schedule/registration, and faculty course workspace are separate compositions. |
| Support/payment | Ticket timeline and invoice review expose domain-specific pending/verification states. |
| QR | Message context and local destination are shown before simulated scan. |
| MFA | Device, location, scope, expiry, and repeated prompt history are visible. |
| Telemetry → Console | Events remain safe, discoverable, and visible in the analyst evidence workspace. |
| Reveal | Completion is rendered on a standalone debrief shell, not inside the victim application. |

## State and interaction coverage

The implementation includes realistic empty, populated, unread, read, pending,
verification-required, success, warning, and completion states where each is
meaningful for the application.

Notable stateful behavior:

- Gemail folder/search filtering and message star/archive/delete/restoration
  actions;
- QuickChat conversation search and unread markers;
- deterministic delivery and separate repeated delivery instances;
- Amazaun/CloudBox two-step target workflows;
- QR scan and MFA repeated-prompt transitions;
- attachment inert-preview state;
- safe end-simulation and completion reveal paths.

The QuickChat composer is intentionally read-only. It supplies a believable
product affordance without creating a free-form exfiltration surface or
persisting user-entered content.

## Verification

The complete verification command passed:

```text
UV_PROJECT_ENVIRONMENT=/tmp/opencode/phisim-final-venv \
UV_CACHE_DIR=/tmp/opencode/phisim-final-uv-cache \
uv run check
```

Result:

```text
120 files already formatted
0 errors, 0 warnings, 0 informations
187 passed, 1 existing Starlette/httpx deprecation warning
```

The dedicated route matrix is in
`tests/simulation/test_ui_realism_flows.py`. It covers Gemail, QuickChat,
Amazaun, CloudBox, QR, and MFA end to end. Full evidence is recorded in
`docs/ai/UI_REALISM_TEST_REPORT.md`.

## Regression follow-up

The follow-up pass addressed the reported visual and lifecycle issues:

- terminal email/SMS lists remain readable, while message/conversation detail
  and action links return `410 Gone` instead of reopening a completed artifact;
- account verification progress is outside the alert content;
- training reveal is explicitly centered;
- TechnoSphere navigation and course-access layout no longer overlap;
- the Lab uses the light workspace treatment again;
- Gemail secondary actions, star controls, and MFA Deny have explicit contrast
  and hover states;
- QuickChat uses the last message in the inbox and removes typing indicators.

`tests/simulation/test_ui_regressions.py` covers these behaviors.

## Safety and privacy result

- No real credentials or personal data were used.
- No submitted values are persisted, logged, broadcast, or returned.
- No real domains, providers, payment processors, carriers, phone numbers, or
  external assets were added.
- QR and message links resolve to local routes.
- Attachments are inert metadata/text previews only.
- MFA and website events contain safe interaction metadata.
- Operator, victim, Console, and reveal templates remain separate.

## Known limitations and follow-up

1. **Connected browser unavailable:** no desktop browser was attached in this
   session, so screenshots, visual diffs, and browser accessibility-tree checks
   remain pending. The route-level matrix passed.
2. **Some controls are representational:** Gemail Sent/Drafts/Spam/Trash and
   CloudBox Recent/Starred/Trash are navigation/context affordances; the
   implemented state persistence is currently strongest for Gemail Inbox,
   Starred, Archive/Delete restoration, search, and read state.
3. **Read-only composer:** QuickChat intentionally does not accept outgoing
   message text because that would add an unnecessary content-capture surface.
4. **Legacy routes:** compatibility routes are visually aligned with the new
   application families, but the primary `/v/{token}/...` routes are the
   canonical delivery path.
5. **Content breadth:** the next content pass can add more scenario-specific
   message threads, invoice variants, and university notices without changing
   the shared safety or telemetry contract.

## Acceptance criteria

| Criterion | Status |
|---|---|
| Gemail feels like a mailbox | PASS |
| QuickChat feels like a messenger | PASS |
| Amazaun feels like an order flow | PASS |
| CloudBox feels like file storage | PASS |
| University scenarios begin in academic context | PASS |
| Support and payment begin in domain context | PASS |
| QR and MFA have distinct application models | PASS |
| Phishing is embedded in believable workflows | PASS |
| Telemetry remains safe and connected to Console | PASS |
| Lab, victim apps, Console, and Reveal are separate | PASS |
| Six-flow route verification | PASS |
| `uv run check` | PASS |
| Connected-browser screenshots/accessibility review | PENDING |

## Commit record

The work was split into atomic commits, in order:

- `bf14245` — UI realism audit;
- `58abd74` — themed victim application baseline;
- `a089aec` — Gemail mailbox;
- `3a938f4` — QuickChat conversations;
- `d531d5c` — Amazaun and CloudBox portals;
- `b03dbd9` — university, support, and payment portals;
- `2674e67` — MFA and QR experiences;
- `3b4d4f3` — operator Lab and analyst Console;
- `4b65827` — legacy mail/chat and attachment flows;
- `a4da961` — standalone training reveal;
- `50325bc` — six-flow UI test matrix;
- `547f0af` and `39ade3b` — compatibility/readability fixes;
- `21cca42` — legacy outcome moved to the standalone reveal;
- `bd4122f` — victim applications own their product chrome;
- `34ebff3` — terminal artifact details close safely;
- `745aa2f` — portal layout, Lab contrast, and control hover fixes;
- `d6b337d` and `88d97ce` — QuickChat typing removal and regression tests;
- `b916694` — regression report update;
- `9358c9e` — Gmail toolbar hover contrast follow-up.

No push was performed.

## Final conclusion

The UI realism pass now changes application information architecture and
interaction patterns, not just visual styling. The local training system is
ready for a connected-browser visual/accessibility pass; all available route,
state, safety, and automated checks are green.
