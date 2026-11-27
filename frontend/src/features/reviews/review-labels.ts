import type { JobReviews, ReviewDirection, ReviewSummary, ReviewTag } from "@/core/api/schemas";

/*
 * Two-way reviews (ADR-011). After sign-off the employer rates the worker
 * and the worker rates the employer. Each review stays hidden until the
 * other side has reviewed too, or 14 days pass, so neither can answer back
 * in kind after reading the other's.
 */

export const TAG_LABEL: Readonly<Record<ReviewTag, string>> = {
  ON_TIME: "On time",
  QUALITY_WORK: "Quality work",
  CLEAN: "Cleaned up",
  FAIR_PRICE: "Fair price",
  PROFESSIONAL: "Polite",
  GOOD_COMMUNICATION: "Kept in touch",
  RELIABLE: "Reliable",
  PAID_ON_TIME: "Paid on time",
  JOB_AS_DESCRIBED: "Job as described",
  RESPECTFUL: "Respectful",
  SAFE_WORKPLACE: "Safe place to work",
};

/** Chips offered when writing a review, by who is reviewing whom. */
export const TAGS_FOR: Readonly<Record<ReviewDirection, readonly ReviewTag[]>> = {
  BUYER_TO_WORKER: ["ON_TIME", "QUALITY_WORK", "CLEAN", "FAIR_PRICE", "PROFESSIONAL"],
  WORKER_TO_BUYER: ["PAID_ON_TIME", "JOB_AS_DESCRIBED", "RESPECTFUL", "SAFE_WORKPLACE"],
};

export function tagLabels(direction: ReviewDirection): string[] {
  return TAGS_FOR[direction].map((tag) => TAG_LABEL[tag]);
}

/** Chip labels back to tags, keeping only the ones this direction allows. */
export function tagsFromLabels(direction: ReviewDirection, labels: readonly string[]): ReviewTag[] {
  return TAGS_FOR[direction].filter((tag) => labels.includes(TAG_LABEL[tag]));
}

function plural(count: number, word: string): string {
  return `${count} ${word}${count === 1 ? "" : "s"}`;
}

/** "★ 4.6 · 12 reviews", "New · 2 reviews" or "No reviews yet". */
export function ratingHeadline(summary: ReviewSummary): string {
  if (summary.count === 0) return "No reviews yet";
  if (summary.is_new || summary.average === null) return `New · ${plural(summary.count, "review")}`;
  return `★ ${summary.average.toFixed(1)} · ${plural(summary.count, "review")}`;
}

/** The most-given tags, as "On time ×12". */
export function topTags(summary: ReviewSummary, limit: number = 4): string[] {
  return Object.entries(summary.tag_counts)
    .slice(0, limit)
    .map(([tag, count]) => `${TAG_LABEL[tag as ReviewTag] ?? tag} ×${count}`);
}

/** "27 Nov", in the reader's time zone. */
function shortDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

/** One line on where this job's reviews stand, for the person viewing. */
export function jobReviewStatus(reviews: JobReviews, otherName: string): string | null {
  const { mine, theirs, is_theirs_waiting, can_review, window_closes_at } = reviews;
  if (mine && theirs) return null;
  if (mine && mine.published_at === null) {
    return window_closes_at
      ? `Your review is shared when ${otherName} reviews you too, or on ${shortDate(window_closes_at)}.`
      : `Your review is shared when ${otherName} reviews you too.`;
  }
  if (!mine && is_theirs_waiting && can_review) {
    return `${otherName} has reviewed you. Leave yours to see what they said.`;
  }
  if (!mine && can_review && window_closes_at) {
    return `You have until ${shortDate(window_closes_at)} to leave a review.`;
  }
  if (!mine && !can_review) return "The time to review this job has passed.";
  return null;
}
