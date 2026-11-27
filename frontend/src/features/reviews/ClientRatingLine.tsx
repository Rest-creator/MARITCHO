"use client";

import { Icon } from "@/components/ui/Icon";
import { useClientReviewsForJob } from "@/features/reviews/hooks";
import { ratingHeadline, topTags } from "@/features/reviews/review-labels";

/**
 * How this client treats workers, from other workers' reviews (ADR-011),
 * before offering a price. The client stays anonymous until booking.
 */
export function ClientRatingLine({ jobId }: { jobId: string }) {
  const reviews = useClientReviewsForJob(jobId);
  if (!reviews.data) return null;
  const { summary, reviews: latest } = reviews.data;
  const tags = topTags(summary, 3);
  const quote = latest.find((review) => review.comment)?.comment;
  return (
    <section className="card card--compact stack" style={{ gap: 6 }} aria-label="About this client">
      <div className="row row--tight" style={{ fontSize: 13, fontWeight: 700 }}>
        <Icon name="users" size={16} />
        This client · {summary.count === 0 ? "New client, no reviews yet" : ratingHeadline(summary)}
      </div>
      {tags.length > 0 && <div className="meta">{tags.join(" · ")}</div>}
      {quote && (
        <p className="meta meta--secondary" style={{ lineHeight: 1.45 }}>
          “{quote}”
        </p>
      )}
    </section>
  );
}
