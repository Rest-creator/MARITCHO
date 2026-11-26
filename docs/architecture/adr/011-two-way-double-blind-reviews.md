# ADR 011: Two-Way, Double-Blind Reviews After Sign-Off

## Status
Accepted and implemented (migration `9d0e1f2a3b4c`; `docs/backlog.md` `TRUST-002`).

## Context
Reviews existed as one-way employer → worker ratings (`POST /jobs/{id}/review`).
The stars, tags and comment were stored and averaged into the worker's
rating, but:
- workers could not rate employers (paid on time, honest about the job, safe
  to work for), against the "design for the worker's worst day" rule;
- the review text was never shown, only the average;
- nothing stopped revenge ratings, and there was no time limit;
- the person reviewed could not reply, and nobody could report an abusive or
  false review;
- one 5-star review outranked a long, steady record;
- the endpoint queried the database from the router, with no use case,
  OpenTelemetry span or structured log.

## Decision
1. **Both sides review after sign-off.** Once a job is `COMPLETED`, the
   employer rates the worker and the worker rates the employer: 1–5 stars,
   up to 3 tags and an optional comment. Each side has its own tags:
   - employer → worker: On time, Quality work, Cleaned up, Fair price, Polite;
   - worker → employer: Paid on time, Job as described, Respectful, Safe place to work.

   The path is unchanged (`POST /jobs/{job_id}/review`), and the direction
   comes from which party is signed in. Every review comes from a real,
   paid, signed-off job.
2. **14-day window, double-blind.** Reviews can be left for 14 days after
   sign-off. A review stays hidden until the other side has reviewed too
   (both are then published together), or until the 14 days pass. Neither
   side can read the other's review before writing their own.
3. **Public reviews, safe display.** Visible reviews are listed on the
   worker's profile (`GET /workers/{id}/reviews`) with a summary: count,
   average, a Bayesian score, the most-given tags, and `is_new`.
   - Reviewers appear by first name and suburb only.
   - A review on a job that had a dispute is labelled as such.
   - Workers see how a client treats workers on the job page, before
     offering (`GET /jobs/{id}/client-reviews`). The client stays anonymous
     until booking, consistent with `OpenJobOut` hiding `buyer_id`.
4. **Fair numbers.** Ratings count only visible reviews: hidden
   (double-blind) and removed reviews never count. Below 3 reviews a person
   is shown as "New" instead of a star average. The Bayesian score (prior
   4.0, weight 5) is exposed for ranking, so one 5-star review can't beat 48
   steady ones.
5. **Reply and report.**
   - The person reviewed may reply once, publicly.
   - They may also report a review. A report does **not** hide it; only OPS
     can (`/ops/reviews/reported`, `/ops/reviews/{id}/moderate`, KEEP or
     REMOVE). Otherwise anyone could bury fair criticism by reporting it.
   - Removing a review hides it and drops it from the rating. Every report
     and decision is audit-logged.
6. **Ratings stay separate from grades.** `Standing.grade` is still earned
   by evidence and vouches (ADR-005, ADR-010); ratings never promote or
   demote anyone.
7. **Clean architecture.** A new `reviews` app (domain, infrastructure,
   interface adapters) owns the `reviews` table. The old router-level
   endpoint and `jobs/infrastructure/review_models.py` are removed. All
   rating aggregates (directory, profile, matching, standing) go through
   one visibility-aware query.

## Consequences
- **Positive:** Workers can warn each other about bad clients. Reviews can't
  be used to retaliate. The written reviews finally do their job for the
  next employer. New workers aren't crushed or inflated by a single review.
  No new external dependency.
- **Negative:** A rating now appears up to 14 days after a job, not
  instantly. Reported reviews stay up until someone at OPS looks, and there
  is no OPS console yet: moderation is API-only, like vetting review (ADR-010).
- **Migration:** existing reviews were all employer → worker and already
  public, so they are backfilled as published `BUYER_TO_WORKER` reviews.
  Downgrading deletes worker → employer reviews. The four new tag values
  stay in the Postgres enum, because Postgres can't drop enum values.

## Not built
- WhatsApp/SMS reminders to review (needs ADR-006 intake).
- Voice-note review comments.
- An employer-facing "reviews about me" page; employers can call
  `GET /clients/{id}/reviews`.
- Automatic flagging of a worker after repeated low ratings.

## Related
- ADR-005, ADR-010 (grades stay evidence-based)
- `docs/architecture/database_schema_design.md` §19
