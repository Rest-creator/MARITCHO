# ADR 003: Two-Tier Quote Breakdown (Labor vs. Materials)

## Status
Accepted and implemented (migration `56ca5ce0be51`; see `docs/backlog.md` `CORE-005`, now `DONE`)

## Context
`docs/requirements/prd.md` already specifies the worker "prices the job standing in front of it" after an on-site diagnostic — no pre-agreed fixed price — which matches the region's volatile construction-material and transport costs. A comparative review of Urban Company's fixed-SKU catalog pricing confirmed that model doesn't survive this volatility; unstandardized housing stock and unpredictable material costs make a single fixed price per task category unworkable here. But today's `Job.quote_amount` / `CrewOrder.quote_amount` (`database_schema_design.md` §1) are a single opaque number the buyer must trust with no breakdown of what's labor versus parts, which weakens the "no overcharging" trust promise `docs/discovery/vision_document.md` names as a core problem to solve.

## Decision
1. Extend the quote step to require two components instead of one: `labor_amount` and `materials_amount`, with `quote_amount` becoming their sum (enforced via a `CHECK` constraint or computed at write time).
2. The existing booking deposit continues to function as the de-facto "diagnostic/scope-inspection fee" already implied by the current booking → quote flow — no separate diagnostic-fee step is introduced; this refines the existing quote step, it does not add a new lifecycle stage.
3. Applies identically to both the Quick Hire (`Job`) and Crew Hire (`CrewOrder`) quote steps.

## Consequences
- **Positive:** Buyers see what they're actually paying for (labor vs. parts), directly reinforcing the "verified, accountable tradesman" trust promise; sets up future reporting on labor-rate consistency across workers/trades without a larger schema change.
- **Negative:** Adds a small amount of quoting friction (two numbers instead of one) and requires a migration plus validation changes on both quote endpoints (`POST /jobs/{id}/quote`, `POST /crew-orders/{id}/quote`).

## Related
- `docs/requirements/prd.md` — "prices the job standing in front of it"
- `docs/architecture/database_schema_design.md` §4 (Job Lifecycle & Ledger State Machine)
- `docs/backlog.md` `CORE-005`
- Rejected alternative: fixed-SKU catalog pricing (Urban Company model) — see "Explicitly Rejected Patterns" in `docs/architecture/system_design.md` §6
