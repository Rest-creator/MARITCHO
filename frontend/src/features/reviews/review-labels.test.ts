import { describe, expect, it } from "vitest";

import type { JobReviews, Review, ReviewSummary } from "@/core/api/schemas";
import {
  jobReviewStatus,
  ratingHeadline,
  tagLabels,
  tagsFromLabels,
  topTags,
} from "@/features/reviews/review-labels";

function summary(overrides: Partial<ReviewSummary>): ReviewSummary {
  return { count: 0, average: null, score: null, is_new: true, tag_counts: {}, ...overrides };
}

const REVIEW: Review = {
  id: "8b0f0c3e-1111-4222-8333-444455556666",
  job_id: "9c1a2b3d-1111-4222-8333-444455556666",
  direction: "BUYER_TO_WORKER",
  rating: 5,
  tags: ["ON_TIME"],
  comment: null,
  created_at: "2026-11-20T10:00:00Z",
  published_at: null,
  visible_after: "2026-12-04T10:00:00Z",
  had_dispute: false,
  reply: null,
  replied_at: null,
};

function jobReviews(overrides: Partial<JobReviews>): JobReviews {
  return {
    job_id: REVIEW.job_id,
    my_direction: "BUYER_TO_WORKER",
    window_closes_at: "2026-12-04T10:00:00Z",
    can_review: true,
    mine: null,
    theirs: null,
    is_theirs_waiting: false,
    ...overrides,
  };
}

describe("ratingHeadline", () => {
  it("says so when there are no reviews", () => {
    expect(ratingHeadline(summary({}))).toBe("No reviews yet");
  });

  it("shows New instead of stars under three reviews", () => {
    expect(ratingHeadline(summary({ count: 1, average: 5, is_new: true }))).toBe("New · 1 review");
  });

  it("shows the average once there are enough reviews", () => {
    expect(ratingHeadline(summary({ count: 12, average: 4.63, is_new: false }))).toBe(
      "★ 4.6 · 12 reviews",
    );
  });
});

describe("tags", () => {
  it("offers different chips to each side", () => {
    expect(tagLabels("BUYER_TO_WORKER")).toContain("Quality work");
    expect(tagLabels("WORKER_TO_BUYER")).toContain("Paid on time");
    expect(tagLabels("WORKER_TO_BUYER")).not.toContain("Quality work");
  });

  it("maps chip labels back to tags for the right direction only", () => {
    expect(tagsFromLabels("WORKER_TO_BUYER", ["Paid on time", "Quality work"])).toEqual([
      "PAID_ON_TIME",
    ]);
  });

  it("lists the most-given tags with counts", () => {
    expect(topTags(summary({ count: 5, tag_counts: { ON_TIME: 4, CLEAN: 2 } }))).toEqual([
      "On time ×4",
      "Cleaned up ×2",
    ]);
  });
});

describe("jobReviewStatus", () => {
  it("explains that a lone review waits for the other side", () => {
    const status = jobReviewStatus(jobReviews({ mine: REVIEW, can_review: false }), "Tendai");
    expect(status).toContain("Your review is shared when Tendai reviews you too");
  });

  it("nudges the person whose review is the missing one", () => {
    const status = jobReviewStatus(jobReviews({ is_theirs_waiting: true }), "the client");
    expect(status).toBe("the client has reviewed you. Leave yours to see what they said.");
  });

  it("says nothing more once both reviews are visible", () => {
    const both = jobReviews({
      mine: { ...REVIEW, published_at: "2026-11-21T10:00:00Z" },
      theirs: { ...REVIEW, direction: "WORKER_TO_BUYER" },
      can_review: false,
    });
    expect(jobReviewStatus(both, "Tendai")).toBeNull();
  });

  it("says when the window has passed", () => {
    expect(jobReviewStatus(jobReviews({ can_review: false }), "Tendai")).toBe(
      "The time to review this job has passed.",
    );
  });
});
