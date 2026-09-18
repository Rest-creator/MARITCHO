# ADR 006: WhatsApp Business API Intake — Scoped, Not Yet Started

## Status
Accepted (decision only — not yet implemented; see `docs/backlog.md` `BACK-009`)

## Context
`docs/discovery/business_case.md` names the WhatsApp channel as explicit **Stage One** scope ("Scope: Web app and WhatsApp channel"), and `docs/discovery/vision_document.md` calls WhatsApp "the primary internet channel" for the target user base — this is not a new idea surfaced by the comparative case-study review (Kandua's "Ask Jess" WhatsApp bot, in particular), it is existing, already-approved product scope that has simply not been built yet. `docs/architecture/system_design.md` §1 previously listed "WhatsApp Business API for SMS/Voice-note fallback" under the Client Tier as if it already existed; no WhatsApp integration code exists anywhere in `app/` — this drift is logged separately as a dev-log entry (`Architecture_and_Design/MARITCHO-2026-09-18-...`).

## Decision
1. Acknowledge WhatsApp Business Cloud API intake as a real, already-scoped Stage One gap, not a "maybe later" idea — but do not start building it opportunistically alongside this documentation pass. It carries a real external dependency (Meta Business API developer/business verification, WhatsApp message-template approval, phone number provisioning) that needs its own scoping/kickoff, not a silent side effect of a docs update.
2. `docs/architecture/system_design.md` §1 is corrected to describe this as planned, not implemented, mirroring how the Redis/background-worker gap was corrected earlier in the same document.

## Consequences
- **Positive:** Documentation now accurately reflects what exists vs. what's approved-but-not-built, so this doesn't get silently rediscovered as a "surprise gap" again.
- **Negative:** None from this decision itself — the underlying gap (WhatsApp not built) remains open and should be prioritized deliberately given it's already Stage One scope, not Stage Two/Three, unlike the other ADRs in this batch.

## Related
- `docs/discovery/business_case.md` — Stage One scope: "Web app and WhatsApp channel"
- `docs/discovery/vision_document.md` — "WhatsApp is the primary internet channel"
- `docs/architecture/system_design.md` §1, §6
- `docs/backlog.md` `BACK-009`
