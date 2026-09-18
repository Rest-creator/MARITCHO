# ADR 004: Compound Geo-Grounding (GPS Pin + Landmark Narrative)

## Status
Accepted and implemented (migration `b4bcfbff527d`; see `docs/backlog.md` `CORE-006`, now `DONE`)

## Context
A comparative review of Zimbabwean and comparable African operating conditions confirmed Bulawayo's high-density and peri-urban suburbs frequently lack reliable street-level addressing — the same condition that leaves ZiMLiNKS's directory model as "call the number and hope." Maricho's current `Job.address` / `CrewOrder.address` is a single free-text field, revealed to the worker only at booking (`database_schema_design.md` §4); nothing structures it for navigation, and nothing captures a GPS coordinate distinct from the suburb-level centroid already used for distance-band matching (§3).

## Decision
1. Add a `landmark_narrative` text field and an optional `latitude`/`longitude` GPS pin to `Job` and `CrewOrder`, captured alongside the existing free-text `address` at request time — a triangulated combination of coordinate, address text, and landmark description, not a replacement for any of them.
2. Scoped as a data-capture addition only. It does not change the existing suburb-level haversine distance-banding used for matching (§3 of `database_schema_design.md`), which remains untouched — the new fields exist purely to help a booked worker physically find the site, not to re-architect discovery-time distance ranking. (Whether suburb-level matching itself needs a finer-grained spatial index is a separate, already-logged and deliberately deferred question — see `docs/backlog.md` `BACK-008`.)

## Consequences
- **Positive:** Meaningfully reduces missed-appointment risk for a real, already-acknowledged Bulawayo addressing gap, at low implementation cost (a couple of nullable columns, no new subsystem).
- **Negative:** GPS pin capture depends on the client (PWA/mobile) requesting device location permission, which isn't guaranteed on every low-tier Android device/browser — the landmark narrative field must remain the reliable fallback, never assumed optional in practice.

## Related
- `docs/architecture/database_schema_design.md` §3 (Suburb Distance Banding), §4 (Job Lifecycle)
- `docs/backlog.md` `CORE-006`, and the related, separately-deferred `BACK-008` (PostGIS/spatial-index matching)
