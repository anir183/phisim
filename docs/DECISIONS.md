# Architecture Decisions

This file records decisions that affect future implementation.

## D001 --- Local simulation by default

**Decision:** PhiSim runs locally/loopback by default.

**Reason:** The project is an educational phishing simulation and should
not accidentally become an externally reachable campaign system.

---

## D002 --- SQLite first

**Decision:** Use SQLite/SQLAlchemy for the initial persistence layer.

**Reason:** The project is a classroom lab and does not need operational
database infrastructure for its first milestones.

A future database can be introduced behind the
infrastructure/application boundary if required.

---

## D003 --- Event-driven telemetry boundary

**Decision:** Simulation components emit structured events through the
telemetry subsystem.

**Reason:** This decouples simulation behavior from persistence and
analyst presentation.

---

## D004 --- No real email/SMS delivery

**Decision:** Email and SMS are represented as simulated
artifacts/workflows.

**Reason:** The educational objective is phishing recognition and
telemetry, not delivery infrastructure.

---

## D005 --- Evidence-oriented analysis

**Decision:** Analysis produces structured indicators and explanations
rather than relying on one opaque phishing score.

**Reason:** The project is intended to teach users what makes an
interaction suspicious.

---

## D006 --- Few abstractions

**Decision:** Do not introduce interfaces/abstract
factories/repositories beyond what concrete duplication or dependency
boundaries justify.

**Reason:** The team is small and the project should remain easy to
understand and merge.

---

## D007 --- Directory ownership

**Decision:** Team members own separate subsystem directories.

**Reason:** Reducing shared-file edits is the primary merge-conflict
prevention mechanism.

---

## D008 --- Email and SMS are local simulated channels

**Decision:** P0 email and SMS use local FastAPI/Jinja2 simulation UIs.
They do not use real delivery APIs.

**Reason:** The project demonstrates phishing recognition and telemetry.
External delivery would add unnecessary credentials, network access,
operational complexity, and safety risk.

**P0 dependency impact:** No additional third-party package is required
specifically for email or SMS.

---

## D009 --- Vertical slice before scenario breadth

**Decision:** The first 2--3 hour team session targets one complete
fake-site → telemetry → analysis → console path before implementing all
P0 channels.

**Reason:** A working vertical slice validates the shared contracts
early and prevents four teams from independently building incompatible
partial systems.
