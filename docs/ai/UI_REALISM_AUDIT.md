# PhiSim UI Realism Audit

**Date:** 2026-09-25
**Branch:** `feature/team-1`
**Scope:** Dedicated UI realism and application-simulation pass

## Executive summary

PhiSim currently has a strong local simulation and telemetry foundation, but
its victim-facing presentation is still too generic. The current visual pass
introduces a `SiteTheme` registry, shared landing/verification partials, and
theme-specific CSS variables. That improves color and copy differentiation,
but it does not yet make the applications structurally distinct.

The central problem is not the absence of theme colors. It is that unrelated
products still inherit the same composition:

```text
page title
→ hero text
→ generic status cards
→ generic “Action required” panel
→ generic form
→ generic result/debrief
```

Gemail, QuickChat, Amazaun, CloudBox, university services, support, payment,
and MFA must be treated as different products. Backend state, safety, session
handling, and telemetry may remain shared. Application information architecture,
layout, density, interaction, and states should not be shared by default.

This audit is the required first pass. No further application rewrite should
begin until the boundaries and implementation order in this document are
accepted.

---

## 1. Current application inventory

| Application surface | Current implementation | Current route family | Current fidelity |
|---|---|---|---|
| Operator Lab | `web/templates/lab.html`, `/lab`, `/api/lab/launch` | Scenario selection and attack observation | Functional operator surface; visually separate from victims |
| Gemail primary | `victim_mail.html`, `victim_email.html`, `victim_attachment.html` | `/mail`, `/v/{token}/mail`, message/link/attachment routes | Mailbox list/detail exists, but still uses a shared fake-app shell and limited folder/state semantics |
| Gemail legacy | `simulation/inbox.html`, `simulation/email.html` | `/inbox`, `/inbox/{id}`, link/attachment routes | Compatibility mailbox; separate markup from primary flow |
| QuickChat primary | `victim_messages.html`, `victim_message.html` | `/messages`, `/v/{token}/messages`, thread/link routes | Conversation list/detail exists, but lacks a true contact/search/composer experience |
| QuickChat legacy | `simulation/sms.html`, `simulation/sms_thread.html` | `/sms`, `/sms/{id}`, link route | Compatibility conversation viewer; not yet a full messaging product |
| Amazaun | Shared `victim_site.html` / `sites/landing.html` path | `/scenario/credential-shopping-001` and primary target route | Marketplace copy/theme exists, but the page is still a generic landing/dashboard/form composition |
| CloudBox | Shared site landing/verification path | `/scenario/credential-cloud-001` and primary target route | Storage copy/theme exists, but no true file browser, shared-file list, breadcrumbs, or storage context |
| UniSecure | Shared site landing/verification path | `/scenario/credential-basic-001` and primary target route | Generic account center; needs an independent university/SSO information architecture |
| UniSecure Support | Shared site landing/verification path | `/scenario/support-portal-001` and primary target route | Ticket copy exists, but the interaction is still a generic form flow |
| PayMate | Shared site landing/verification path | `/scenario/credential-payment-001` and primary target route | Payment copy/theme exists, but not a distinct payment product workflow |
| MAKExam | Shared site landing/verification path | `/scenario/mak-exam-001` and primary target route | Academic copy exists, but lacks notices, registration, exam, result, and academic calendar context |
| TechnoSphere | Shared site landing/verification path | `/scenario/technosphere-001` and primary target route | Course copy exists, but lacks a faculty/LMS workspace model |
| NimbusID MFA | `victim_mfa.html`, `simulation/mfa.html` | `/v/{token}/mfa/...`, `/mfa/...` | Device prompt styling exists, but is still a shared auth-shaped surface rather than a full MFA product state model |
| QR destination | `victim_qr.html`, `simulation/qr.html` | `/v/{token}/qr/...`, `/qr/...` | QR context is distinct, but destination state is still mostly a route transition |
| Training reveal | `victim_reveal.html`, `simulation/outcome.html`, MFA outcome templates | Result/end routes | Separate debrief surface exists and should remain separate from victim applications |
| Analyst Console | `console.html`, `console.js` | `/console`, analysis/event APIs | Separate operator-facing telemetry surface; should not share victim application layouts |

### Reference interpretation

The supplied screenshots are references for information architecture and density,
not assets to copy. The intended parody targets are:

- Gemail: compact three-pane mailbox with folders, categories, dense list, and message detail.
- QuickChat: split-pane conversation list, contact header, bubbles, timestamps, and composer.
- Amazaun: marketplace header/search/navigation, order/product hierarchy, delivery state, and contextual actions.
- CloudBox: file sidebar, breadcrumbs, recent/shared files, storage/activity context, and file metadata.
- MAKAUT/Techno-style references: institutional navigation, notices, dashboards, examination/result areas, and academic context.

All implementations remain fictional, local, and free of real logos,
credentials, domains, providers, and network calls.

---

## 2. Current routes

### Operator and platform

| Route | Purpose |
|---|---|
| `GET /lab` | Scenario Lab and attack launcher |
| `POST /api/lab/launch` | Starts a local run/attack |
| `GET /api/lab/attacks/{attack_id}` | Operator attack status page/API |
| `POST /api/lab/attacks/{attack_id}/abandon` | Operator-controlled abandonment |
| `GET /api/scenarios` | Scenario catalog |
| `GET /api/sessions` | Session listing |
| `GET /api/events` | Event retrieval |
| `GET /api/events/ws` | Live event WebSocket |
| `GET /api/analysis/sessions/{session_id}` | Session analysis/timeline |
| `GET /console` | Analyst console |

### Primary victim environment

| Route | Purpose |
|---|---|
| `GET /mail` | Gemail/environment entry point |
| `GET /messages` | QuickChat/environment entry point |
| `GET /v/{token}/status` | Delivery/lifecycle status polling |
| `GET /v/{token}/mail` | Primary mailbox |
| `GET /v/{token}/mail/{message_id}` | Primary message detail |
| `GET /v/{token}/mail/{message_id}/link` | Message link funnel |
| `GET /v/{token}/mail/{message_id}/attachment` | Inert attachment preview |
| `GET /v/{token}/messages` | Primary conversation list |
| `GET /v/{token}/messages/{thread_id}` | Primary conversation detail |
| `GET /v/{token}/messages/{thread_id}/link` | Message link funnel |
| `GET /v/{token}/site/{scenario_id}` | Primary target application |
| `POST /v/{token}/site/{scenario_id}/continue` | Target application interaction |
| `POST /v/{token}/site/{scenario_id}/finish` | Target application final action |
| `GET /v/{token}/site/{scenario_id}/result` | Compatibility completion route |
| `POST /v/{token}/site/{scenario_id}/end` | Safe user-requested simulation completion |
| `GET /v/{token}/qr/{scenario_id}` | Primary QR context |
| `GET /v/{token}/qr/{scenario_id}/scan` | Simulated QR scan |
| `GET/POST /v/{token}/mfa/{scenario_id}/{step}` | Primary MFA prompt/response |

### Legacy compatibility routes

| Route | Purpose |
|---|---|
| `GET /inbox` | Legacy mailbox |
| `GET /inbox/{message_id}` | Legacy message detail |
| `GET /inbox/{message_id}/link` | Legacy link funnel |
| `GET /inbox/{message_id}/attachment...` | Legacy inert attachment routes |
| `GET /sms` | Legacy conversation list |
| `GET /sms/{thread_id}` | Legacy conversation detail |
| `GET /sms/{thread_id}/link` | Legacy link funnel |
| `GET/POST /scenario/{scenario_id}` | Legacy target application |
| `GET/POST /scenario/{scenario_id}/username` | Legacy identifier step |
| `GET/POST /scenario/{scenario_id}/password` | Legacy password/confirmation step |
| `POST /scenario/{scenario_id}/end` | Legacy safe completion |
| `GET /qr/{scenario_id}` | Legacy QR context |
| `GET /mfa/{scenario_id}/{step}` | Legacy MFA context |

---

## 3. Current scenario → UI mapping

| Scenario family | Artifact/target | Current UI path | Current problem |
|---|---|---|---|
| Credential phishing | Email/SMS/QR → UniSecure | Shared target landing → shared verification | Good safety/lifecycle foundation, but generic auth-shaped target |
| Shopping | SMS/email → Amazaun | Shared target landing → address/confirmation | Copy says marketplace, structure is still generic dashboard/form |
| Cloud storage | Email → CloudBox | Shared target landing → work email/password | Copy says storage, structure is still generic dashboard/form |
| Payment/BEC | Email → PayMate | Shared target landing → billing/confirmation | Payment context is not a payment product state machine |
| Support | Email → UniSecure Support | Shared target landing → employee/verification | Support context is not a ticket/agent/helpdesk product |
| Academic | UniSecure/TechnoSphere/MAKExam targets | Shared target landing → registration/course/password | No notices, dashboard, academic calendar, result, or course workspace model |
| Spear/whaling/clone/urgency | Gemail artifacts → target sites | Catalog-specific copy inside shared Gemail/target UI | Email techniques differ in text but not enough in application workflow |
| QR | QR artifact → UniSecure | QR card → target landing | QR is distinct, but destination preview and application state are thin |
| MFA fatigue | NimbusID | Repeated prompt route | Prompt sequence exists; device/application context needs deeper product modeling |
| Attachment/link spoofing | Gemail artifact → target | Inert preview/link flow | Artifact context exists, but surrounding application workflow is not product-specific |
| SMS smishing | QuickChat → Amazaun/Support | Conversation list → link → target | Conversation product is not yet a real messaging workspace |

---

## 4. Shared components

The following are legitimate shared infrastructure or primitives:

- `shell.html` and `simulation/base.html` application scaffolding.
- `victim_base.html` and `environment_base.html` local-only safety framing.
- Local cookie/session/attack context.
- Delivery polling and deterministic timing.
- End-simulation POST handling and completion state.
- Safe form primitives and credential metadata validation.
- Event emission, persistence, WebSocket delivery, analysis, and console APIs.
- Local asset policy and no-egress guardrails.
- Basic accessibility primitives: labels, focus states, semantic buttons, and status text.
- A small theme registry may provide names, colors, and content metadata.

## 5. Components that should **not** be shared

These should become application-specific components or partials:

- Gemail folder/category/message-list/message-detail layout.
- QuickChat contact list, conversation header, bubbles, composer, and typing state.
- Amazaun marketplace header, search, category bar, order/product cards, delivery timeline, and cart/account context.
- CloudBox file sidebar, breadcrumbs, file/folder grid/list, storage meter, sharing panel, and activity panel.
- University navigation, notices, examination/result/attendance/calendar modules, and student/faculty dashboards.
- Support ticket, agent, incident, and knowledge-base components.
- Payment transaction, invoice, approval, and payment-status components.
- MFA device, request, location, and approval components.
- QR destination preview and scan-state components.
- Scenario-specific CTA labels, empty states, and workflow transitions.
- Training reveal layout, which should be separate from every victim application.

A shared `landing.html` or `verification.html` may provide a tiny safety/footer
primitive, but must not define the application's primary information
architecture.

---

## 6. Current visual problems

1. **Shared composition:** Gemail, QuickChat, Amazaun, CloudBox, and university pages all inherit hero/card/action/form proportions.
2. **Color before structure:** Theme variables change the palette, but list density, navigation, hierarchy, and component relationships remain generic.
3. **Overuse of cards:** The applications use repeated rounded surfaces, shadows, and status cards where real products use toolbars, lists, rows, panes, and dense metadata.
4. **Generic page hierarchy:** The same title/hero/action sequence is used regardless of whether the product is a mailbox, marketplace, file store, or university portal.
5. **Insufficient application identity:** Logos, navigation labels, and product-specific controls are mostly text inside a common shell.
6. **Weak empty/populated distinction:** Empty states exist, but populated states do not yet have the expected density and relationship structure of the reference products.
7. **Visual safety is too prominent:** The persistent safety strip is appropriate, but the current application surfaces need to feel like products first while remaining clearly local/fictional in metadata and reveal.
8. **Responsive assumptions:** Shared card layouts do not yet express the distinct desktop information architectures of mailbox, messenger, marketplace, and file storage.

## 7. Current interaction problems

1. Most target applications still begin with a generic “action required” form rather than a believable application context.
2. Gemail and QuickChat have list/detail routes but lack full product interactions such as search, folders, archive/star/delete state, contact filtering, or composer behavior.
3. Amazaun does not yet expose an order list → order detail → delivery state progression.
4. CloudBox does not yet expose shared files → file detail → verification progression.
5. University scenarios do not begin inside a notice/dashboard/course context.
6. Scenario-specific phishing techniques are mostly differentiated by catalog copy and target form fields, not by distinct workflows.
7. The result/reveal boundary is safer than before, but compatibility routes still expose a generic result abstraction.
8. The operator Lab and victim applications are separate in intent, but visual primitives can still blur their boundary.
9. Local deterministic state transitions are present, but application-level pending/loading/expired/failure states are incomplete.

---

## 8. Missing application states

### Gemail

- Empty inbox
- Delivered/unread message
- Read message
- Selected message
- Search results
- Starred
- Archived
- Drafts
- Spam/Trash
- Attachment state
- Link-hover/destination-preview state

### QuickChat

- Empty conversation list
- Conversation search/filter
- Unread thread
- Selected thread
- Incoming message
- Outgoing/local reply affordance
- Typing indicator
- Delivery/read receipt
- Link preview
- Composer focus/disabled state

### Amazaun

- Marketplace home
- Category/search state
- Order list
- Order detail
- Delivery pending
- Address confirmation
- Payment issue
- Account/sign-in state
- Order success/failure state

### CloudBox

- My Files
- Recent
- Shared
- Starred
- Trash
- Folder/file list
- File detail
- Sharing panel
- Storage meter
- Activity panel
- Verification-required state

### University applications

- Student/faculty dashboard
- Notices
- Examination/registration
- Results
- Attendance
- Academic calendar
- Profile
- Fee/payment information
- Notice detail → verification flow

### MFA/support/payment

- Pending request
- Request details
- Expired request
- Approval/denial state
- Support ticket state
- Agent/help article state
- Payment authorization state

---

## 9. Missing scenario-specific behavior

- Credential phishing should begin in a believable account/mailbox/storage context and use an account-specific verification surface.
- Spear phishing should visibly use a known course/person/administrative context.
- Whaling should use an executive/finance workflow and unusual payment/administrative request.
- Clone phishing should show a familiar prior thread with a changed action or destination.
- Urgency should include a believable deadline/countdown/status context, not only warning copy.
- Tech support should begin in a ticket or security-alert context.
- QR should include a message/poster context, destination preview, and scan state.
- Smishing should be a real conversation with message arrival and link context.
- Attachment phishing should include a document preview and a believable follow-up action.
- Link spoofing should expose visible/actual destination mismatch inside a realistic message or application context.
- BEC should use invoice/thread/payment-review context.
- MFA fatigue should show repeated device requests and changing fatigue state.

---

## 10. Proposed UI architecture

```text
Shared simulation infrastructure
├── session/attack state
├── delivery timing
├── safety/local-only controls
├── telemetry/event emission
├── analysis/console APIs
└── end-simulation completion

Application-specific victim UI
├── Gemail application
│   ├── mailbox shell
│   ├── folders/categories
│   ├── message list/detail
│   └── mail actions
├── QuickChat application
│   ├── conversation list
│   ├── contact header
│   ├── message timeline
│   └── composer
├── Amazaun application
│   ├── marketplace navigation
│   ├── order/product state
│   ├── delivery state
│   └── account action
├── CloudBox application
│   ├── file navigation
│   ├── file/folder content
│   ├── storage/activity context
│   └── sharing action
├── University applications
│   ├── student services shell
│   ├── faculty/LMS shell
│   ├── notices/dashboard modules
│   └── academic workflows
├── Specialized applications
│   ├── support desk
│   ├── payment portal
│   ├── MFA device prompt
│   └── QR destination
└── Training reveal
    ├── debrief
    ├── indicators
    ├── event summary
    └── safe response guidance
```

### Theme registry role

The existing `SiteTheme` registry should remain useful for:

- key/name/mark
- palette tokens
- local fictional copy
- application type
- route ownership

It should not dictate a universal page structure. Each application should
select its own template/component family based on the application type.

### State ownership

Backend attack/session state remains authoritative. Application UI state should
be derived from:

- delivered artifact IDs
- read/open state
- current workflow step
- scenario-specific state fields
- deterministic timing profile

UI-only state such as selected folder, search text, selected file, or open
conversation should remain local and deterministic unless it affects telemetry.

---

## 11. Implementation order

### Pass 1 — Audit

- Create and review this document.
- Confirm route/template ownership.
- Identify shared versus application-specific boundaries.

### Pass 2 — Application architecture

- Introduce application-specific template families.
- Keep shared safety, state, telemetry, and completion primitives.
- Separate Lab, victim applications, and reveal.

### Pass 3 — Gemail

- Replace the generic fake inbox with a real mailbox shell.
- Add folders, categories, list/detail, search, and message state.
- Verify delivery and telemetry independently.

### Pass 4 — QuickChat

- Replace the generic conversation list with a real messaging shell.
- Add search, contact/thread states, bubbles, timestamps, typing, and composer affordances.
- Verify delivery and telemetry independently.

### Pass 5 — Amazaun

- Build marketplace navigation/search.
- Add order list/detail/delivery states.
- Embed the phishing action in an order workflow.

### Pass 6 — CloudBox

- Build file navigation and recent/shared content.
- Add file detail, storage/activity context, and sharing workflow.

### Pass 7 — University applications

- Build separate fictional student and faculty shells.
- Add notices, academic modules, and scenario-specific context.

### Pass 8 — Specialized flows

- Differentiate QR, MFA, support, attachment, link spoofing, spear/whaling, and BEC workflows.

### Pass 9 — Operator Lab

- Keep the Lab visually and behaviorally separate.
- Add launch/reset/observation controls without copying victim UI.

### Pass 10 — Integration verification

- Run the complete operator → victim → telemetry → analysis → console → reveal path.
- Perform manual demonstrations and record evidence.

### Pass 11 — Reports

Create:

- `docs/ai/UI_REALISM_TEST_REPORT.md`
- `docs/ai/UI_REALISM_FINAL_REPORT.md`

Include known weaknesses rather than hiding them.

---

## Acceptance criteria

The pass is complete only when:

1. Removing the PhiSim logo still leaves each application recognizable as its product type.
2. Gemail feels like a mailbox, not a dashboard.
3. QuickChat feels like a messenger, not a generic two-column card page.
4. Amazaun feels like a marketplace/order flow, not a colored form.
5. CloudBox feels like a file/storage application, not a generic account portal.
6. University scenarios begin inside believable academic context.
7. Messages and conversations arrive through the local delivery state.
8. Different phishing techniques produce visibly different workflows.
9. The phishing action is embedded inside the application context.
10. Training reveal occurs only after the meaningful interaction or explicit safe end action.
11. Telemetry remains safe, observable, and connected to analysis/console.
12. `uv run check` passes.
13. Manual demonstration evidence is recorded.
14. No real credentials, services, domains, or outbound network calls are introduced.

---

## Current audit conclusion

The current theme pass is a useful foundation, but it is not sufficient as a
final realism implementation. The next implementation phase should replace
the universal application body with product-specific information architecture,
starting with Gemail and QuickChat, followed by Amazaun and CloudBox. Backend
contracts and safety guarantees should remain stable while the presentation
layer becomes genuinely application-specific.
