# ADR 002: Cash-Settlement and Multi-Currency Ledger Rails

## Status
Accepted and implemented (revised 2026-09-18 — see "Revision" below; migration `22a5feb5dcce`; see `docs/backlog.md` `LEDG-001`, now `DONE`)

## Context
Zimbabwe's skilled-trades economy settles overwhelmingly in physical USD cash, with EcoCash mobile money and a volatile ZWG as secondary rails — `docs/discovery/business_case.md`'s own "Holding Funds" note already anticipates this ("Funds in Zimbabwe will likely run on a licensed rail... rather than Maricho holding balances directly"). A comparative review of Thumbtack, Taskrabbit, Airtasker, and Urban Company confirmed all of them assume a card/bank/UPI rail Maricho's target users mostly don't have; a card-escrow-only ledger would exclude the majority of real transactions in this market. Today's `ledger_entries`/`crew_order_ledger_entries` tables record a currency-agnostic `amount` and assume the platform holds and releases the full transacted sum — workable for a digital/EcoCash-funded booking, but meaningless for a cash-in-hand job, where Maricho never touches the money at all.

**Critically, `business_case.md`'s "Financial Modeling & Revenue Streams" section states the monetization model explicitly:** *"Maricho is built to monetize the demand side (the buyer) while remaining entirely free for the supply side (the worker). Charging the worker selects for desperation, not skill."* Quick Hire's fee is "a percentage of the job, charged to the buyer and disclosed before booking." Any cash-settlement design that extracts money from the worker — even indirectly, via a wallet — violates this.

## Decision
1. Ledger entries carry an explicit `currency` (`USD`, `ECOCASH`, `ZWG`) alongside `amount`, rather than assuming one implicit currency.
2. **The platform's fee is collected digitally from the buyer, at booking time, via EcoCash** — this extends the existing `deposit_amount`/`DEPOSIT_HELD` mechanism (§4 of `database_schema_design.md`), which already runs at exactly that point in the lifecycle. The deposit is not necessarily the full job value; at minimum it covers the platform's take.
3. The worker's portion of the agreed price is collected directly from the buyer, in physical cash, off-platform. Maricho never holds or releases that portion for a cash-settled job, and never debits anything from the worker at any point — there is no worker-side wallet, no worker top-up, no worker commission debit.
4. Digital-rail jobs where the buyer pays the *entire* amount via EcoCash (not just the deposit/fee) keep the existing deposit-hold → balance-committed → release lifecycle unchanged, now tagged with a currency, exactly as before.
5. This is an adjustment to the existing `LEDGER_ENTRIES`/`CREW_ORDER_LEDGER_ENTRIES` tables (a currency column) plus a real EcoCash collection integration for the buyer-side deposit/fee payment — not a rebuild into a full multi-rail double-entry accounting core. That heavier investment is warranted only once transaction volume actually demands full auditable double-entry bookkeeping, not on day one.

## Consequences
- **Positive:** Matches the dominant real-world settlement method instead of assuming a rail Maricho's users mostly don't have; secures platform revenue via a real digital collection from the buyer, consistent with the "buyer pays, worker is free" model; introduces no new failure mode for workers (no wallet to keep funded, no risk of losing job dispatch over a balance).
- **Negative:** The EcoCash collection integration is a real external dependency (merchant credentials, configured by OPS at runtime — see the EcoCash gateway config in `database_schema_design.md` §10) that cannot be tested against the live service until real credentials exist; the integration code is env/config-gated and built against the general shape of a merchant collection API, not a confirmed EcoCash API spec, since no such spec was available to verify against at build time.

## Revision (2026-09-18)
The original version of this ADR specified a worker-side pre-funded commission wallet, debited on cash-job completion. That design was caught and rejected *before implementation* — see the dev-log entry `Architecture_and_Design/MARITCHO-2026-09-18-adr-002-cash-settlement-design-contradicted-worker-never-charged-principle.md` — because it directly contradicted `business_case.md`'s explicit "free for the supply side" principle. This revision replaces it with the buyer-funded model above.

## Related
- `docs/discovery/business_case.md` — "Financial Modeling & Revenue Streams": buyer-funded fee model, and the "Holding Funds" note (the original mandate this formalizes)
- `docs/backlog.md` `LEDG-001`
- Rejected alternative: pure card/bank escrow as the *only* rail (Airtasker/Taskrabbit model) — see "Explicitly Rejected Patterns" in `docs/architecture/system_design.md` §6
- Rejected alternative (this revision): a worker-side pre-funded commission wallet — see the dev-log entry above
