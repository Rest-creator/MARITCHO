# ADR 005: Progressive Vetting Tiers Replace Institution-Dependent Checks

## Status
Accepted and implemented (migration `c776d5d98df3`; see `docs/backlog.md` `CORE-007`, now `DONE`)

## Context
A comparative review of Checkatrade's 12-point vetting model (identity verification, credit checks, county court judgment searches, formal trade-body accreditation such as Gas Safe/NICEIC) confirmed most of those checks depend on institutions and public verification APIs that don't exist or aren't queryable in Zimbabwe — there is no open government ID-verification API, and the trades sector is dominated by informal labor with no formal-licensing-body equivalent. The existing `Skill.grade` / `Standing.grade` (`GradeEnum`: `REGISTERED`, `IDENTIFIED`, `APPRENTICE`, `JOURNEYMAN`, `EXPERT`) already models a progression, but per the still-open item from the architecture review, nothing currently sets `Skill.grade` — there is no defined workflow for what evidence promotes a worker from one tier to the next.

## Decision
1. Define (not yet build) a progressive, evidence-based promotion path using verification methods that actually work in this market:
   - `REGISTERED` → `IDENTIFIED`: a photographed national ID.
   - `IDENTIFIED` → `APPRENTICE`: one or more contactable references.
   - `APPRENTICE` → `JOURNEYMAN`/`EXPERT`: a vouch from an existing higher-tier ("master") artisan already on the platform.
2. This directly answers the open question left by the grade-enum finding ("decide and build whatever sets `Skill.grade` in practice") — the mechanism is now specified, though not yet implemented.
3. A vouch only counts from a worker who is themselves `JOURNEYMAN` or higher and has no prior flagged fraudulent-vouch strikes — this abuse-prevention rule is part of the decision, not a later add-on, since peer vouching is otherwise trivially gameable (workers vouching for friends).

## Consequences
- **Positive:** An achievable trust-building path with no dependency on institutions that don't exist locally; reuses the platform's own worker graph (peer vouching) as a trust primitive, fitting a market that already runs on social networks and referrals far better than a paperwork checklist would.
- **Negative:** Peer vouching still carries residual gaming risk even with the higher-tier-only restriction (a colluding cluster of workers vouching for each other); this needs monitoring once the workflow exists, not just the tier structure alone.

## Related
- `docs/discovery/vision_document.md` — "Skill is invisible... issue evidence... and an earned grade"
- `docs/requirements/prd.md` §"Skill: Trade, grade, proof"
- `docs/backlog.md` `CORE-007`
- Rejected alternative: Checkatrade's institution-dependent 12-point check — see "Explicitly Rejected Patterns" in `docs/architecture/system_design.md` §6
