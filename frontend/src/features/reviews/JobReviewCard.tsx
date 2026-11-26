"use client";

import { useState } from "react";

import { Icon } from "@/components/ui/Icon";
import type { Review } from "@/core/api/schemas";
import { ReviewPanel, type ReviewDraft } from "@/features/jobs/ReviewPanel";
import { useSubmitReview } from "@/features/jobs/hooks";
import { useJobReviews } from "@/features/reviews/hooks";
import {
  jobReviewStatus,
  TAG_LABEL,
  tagLabels,
  tagsFromLabels,
} from "@/features/reviews/review-labels";

type Props = {
  jobId: string;
  /** First name or "the client" / "the worker". */
  otherName: string;
};

function Given({ review, title }: { review: Review; title: string }) {
  return (
    <div className="stack" style={{ gap: 4 }}>
      <div className="meta" style={{ fontWeight: 700 }}>
        {title}
      </div>
      <div className="text-amber" aria-label={`${review.rating} out of 5 stars`}>
        {"★".repeat(review.rating)}
        <span style={{ opacity: 0.3 }}>{"★".repeat(5 - review.rating)}</span>
      </div>
      {review.tags.length > 0 && (
        <div className="meta">{review.tags.map((tag) => TAG_LABEL[tag]).join(" · ")}</div>
      )}
      {review.comment && <p style={{ fontSize: 14, lineHeight: 1.5 }}>{review.comment}</p>}
    </div>
  );
}

/**
 * Reviews on a signed-off job, for either party (ADR-011): leave yours,
 * see whether it's shared yet, and read theirs once both are in.
 */
export function JobReviewCard({ jobId, otherName }: Props) {
  const reviews = useJobReviews(jobId);
  const submit = useSubmitReview();
  const [draft, setDraft] = useState<ReviewDraft>({ stars: 0, tags: [], note: "" });
  const [error, setError] = useState<string | null>(null);

  if (!reviews.data) return null;
  const data = reviews.data;
  const direction = data.my_direction;
  const isAboutWorker = direction === "BUYER_TO_WORKER";
  const status = jobReviewStatus(data, otherName);

  async function send(): Promise<void> {
    if (draft.stars < 1) {
      setError("Tap a star rating first.");
      return;
    }
    setError(null);
    try {
      await submit.mutateAsync({
        jobId,
        rating: draft.stars,
        tags: tagsFromLabels(direction, draft.tags),
        ...(draft.note.trim() === "" ? {} : { comment: draft.note.trim().slice(0, 1000) }),
      });
      await reviews.refetch();
    } catch (failure: unknown) {
      setError(failure instanceof Error ? failure.message : "Your review didn't go through.");
    }
  }

  return (
    <section className="stack" style={{ gap: 12 }} aria-label="Reviews">
      {data.can_review && !data.mine && (
        <>
          <ReviewPanel
            value={draft}
            onChange={setDraft}
            tags={tagLabels(direction)}
            heading={
              isAboutWorker ? `How did ${otherName} do?` : `How was ${otherName} to work for?`
            }
            description={`Only shown once ${otherName} has reviewed you too, or after 14 days — so nobody reviews in reply.`}
          />
          {error && (
            <p className="field-error" role="alert">
              {error}
            </p>
          )}
          <button
            type="button"
            className="btn btn--block"
            disabled={submit.isPending}
            onClick={() => void send()}
          >
            <Icon name="star" size={16} />
            Send review
          </button>
        </>
      )}

      {(data.mine || data.theirs || status) && (
        <div className="card stack" style={{ gap: 12 }}>
          {status && (
            <p className="meta meta--secondary" role="status" style={{ lineHeight: 1.45 }}>
              {status}
            </p>
          )}
          {data.theirs && <Given review={data.theirs} title={`What ${otherName} said`} />}
          {data.mine && <Given review={data.mine} title="Your review" />}
        </div>
      )}
    </section>
  );
}
