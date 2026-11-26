# ADR 010: Private Identity Documents and Reviewed Verification Badges

## Status
Accepted and implemented (migration `8c9d0e1f2a3b`; `docs/backlog.md` `TRUST-001`). Amends ADR-005's `REGISTERED` → `IDENTIFIED` step.

## Context
ADR-005 made a "photographed national ID" the evidence for `IDENTIFIED`, and
WEB-023 added an optional Police Clearance photo as the prerequisite for the
"Police Cleared" badge. As built, both were granted the moment *any* URL was
saved in `worker_vetting.id_photo_url` / `police_clearance_url`:

- nobody looked at the document, so a photo of anything earned the grade and badge;
- the URL was free-form, so it did not even have to be an upload;
- a police clearance photo alone also satisfied the identity floor.

Zimbabwe has no open government API to check a national ID, and the Zimbabwe
Republic Police (ZRP) offers no online or QR check for clearance certificates
(ZRP Form 143 / 143A are issued after in-person fingerprinting at CID).
Verification therefore has to be done by Maritcho itself.

We considered not keeping the documents at all (check them in memory and
throw them away). We decided against it: without the image a reviewer can't
look again, a disputed badge can't be re-checked, and low-confidence cases
would have nowhere to go.

## Decision
1. **Documents are kept, privately.** The ID and clearance photos stay in
   the existing media store (`POST /media/upload`). Only the worker who
   uploaded them and `OPS` staff can open them (`GET /media/{id}` already
   enforces owner-or-OPS). They are never shown to employers or other
   workers, and no public or employer-facing schema returns their URLs.
2. **Only real, owned uploads are accepted.** The vetting submit endpoints
   accept only `/media/{id}` for an image the same worker uploaded; any other
   URL is rejected with 422.
3. **Badges come from a review result, not from a photo existing.** Each
   document has a status: `PENDING` (submitted, waiting), `VERIFIED`, or
   `REJECTED` (with a reason the worker sees). Submitting or replacing a
   document sets it back to `PENDING`.
   - `IDENTIFIED` (and everything built on it) requires the ID to be `VERIFIED`.
     A police clearance no longer counts as identity on its own.
   - "Police Cleared" requires the clearance to be `VERIFIED` **and** not
     expired. On approval the reviewer records the issue date; the badge
     expires 12 months later (`POLICE_CLEARANCE_VALID_DAYS`).
   - A clearance can only be approved once the ID is `VERIFIED`, so the
     name and ID number on the certificate can be matched against it.
4. **OPS reviews documents.** `GET /ops/vetting/pending` lists the waiting
   documents. `POST /ops/vetting/{worker_id}/id` and
   `POST /ops/vetting/{worker_id}/police-clearance` approve or reject them.
   - When approving an ID, the reviewer records the name as printed. The
     reviewer also types the ID number, which is checked against the
     Zimbabwe layout (district, 6–7 digits, letter, district).
   - Only a keyed HMAC-SHA256 hash of the ID number is stored
     (`ID_NUMBER_HASH_KEY`, falling back to `SECRET_KEY`). It is unique, so
     one national ID can verify only one account. The raw number is never
     stored or logged.
   - Every decision records who made it and when, and is audit-logged.
5. **Migration of existing data.** Rows that already hold a photo become
   `PENDING`. Their grade and badge drop until a reviewer approves them.
   This is deliberate: those badges were never checked.

## Consequences
- **Positive:** The badges now mean what they say. A reviewer can re-open the
  document later. Duplicate accounts on one ID are blocked. The worker sees
  why a document was rejected and can resubmit. No new external dependency.
- **Negative:** Someone at Maritcho has to review every document, so badges
  are no longer instant. Workers who uploaded before this change lose their
  `IDENTIFIED` grade and Police Cleared badge until reviewed.
- **Negative:** Maritcho now holds identity documents, which are personal
  data under Zimbabwe's Cyber and Data Protection Act. They need consent
  wording, a retention rule and access logging. Access is limited to the
  owner and OPS. A retention and deletion policy is a follow-up.
- **Badge wording:** "Police Cleared" means Maritcho staff checked the
  certificate and matched it to the verified ID. It does not mean ZRP
  confirmed it, because no ZRP verification service exists.

## Future (not built)
Open-licence checks could pre-fill and speed up the review. None of them
replaces the reviewer:
- RapidOCR or Tesseract (Apache 2.0) to read the name and number;
- OpenCV Zoo YuNet and SFace to match a selfie against the ID photo;
- MiniFASNet to check the selfie is a live person.

Avoid InsightFace's pretrained models: their licence is non-commercial.

## Related
- ADR-005 Progressive vetting tiers (amended step 1)
- `docs/architecture/database_schema_design.md` §18
- `backend/app/apps/media/README.md` (owner-or-OPS download rule)
