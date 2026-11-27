"use client";

import { useState, type FormEvent } from "react";

import { Icon } from "@/components/ui/Icon";
import type { PublicReview, ReviewPage } from "@/core/api/schemas";
import { useReplyToReview, useReportReview } from "@/features/reviews/hooks";
import { ratingHeadline, TAG_LABEL, topTags } from "@/features/reviews/review-labels";

type Props = {
  page: ReviewPage;
  /** "What clients say" / "What workers say". */
  title: string;
  /** The person reviewed is looking: they can reply once and report. */
  ownerWorkerId?: string;
  emptyText?: string;
};

function Stars({ rating }: { rating: number }) {
  return (
    <span aria-label={`${rating} out of 5 stars`} className="text-amber" style={{ fontSize: 13 }}>
      {"★".repeat(rating)}
      <span style={{ opacity: 0.3 }}>{"★".repeat(5 - rating)}</span>
    </span>
  );
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

/** Reviews about one person, with a summary. Used on profiles and the worker's own page. */
export function ReviewList({ page, title, ownerWorkerId, emptyText }: Props) {
  const { summary, reviews } = page;
  const tags = topTags(summary);
  return (
    <section className="card stack" style={{ gap: 12 }} aria-label={title}>
      <div className="row row--between" style={{ alignItems: "baseline" }}>
        <h2 style={{ fontSize: 15, fontWeight: 700 }}>{title}</h2>
        <span className="meta" style={{ fontWeight: 700 }}>
          {ratingHeadline(summary)}
        </span>
      </div>
      {summary.is_new && summary.count > 0 && (
        <p className="meta meta--secondary">
          A star rating shows once there are 3 reviews, so one review can&apos;t make or break
          anyone.
        </p>
      )}
      {tags.length > 0 && (
        <div className="chip-list" style={{ gap: 6 }}>
          {tags.map((tag) => (
            <span key={tag} className="tag">
              {tag}
            </span>
          ))}
        </div>
      )}
      {reviews.length === 0 ? (
        <p className="meta meta--secondary">
          {emptyText ?? "No reviews yet. Reviews appear after signed-off jobs."}
        </p>
      ) : (
        <ul className="stack" style={{ gap: 12, listStyle: "none", padding: 0, margin: 0 }}>
          {reviews.map((review) => (
            <ReviewItem key={review.id} review={review} ownerWorkerId={ownerWorkerId} />
          ))}
        </ul>
      )}
    </section>
  );
}

function ReviewItem({ review, ownerWorkerId }: { review: PublicReview; ownerWorkerId?: string }) {
  return (
    <li
      className="stack"
      style={{ gap: 6, paddingTop: 12, borderTop: "1px solid var(--line-subtle)" }}
    >
      <div className="row row--between">
        <Stars rating={review.rating} />
        <span className="meta">{formatDate(review.created_at)}</span>
      </div>
      <div className="meta">
        {review.reviewer_name}
        {review.reviewer_suburb ? ` · ${review.reviewer_suburb}` : ""}
        {review.had_dispute && " · There was a dispute on this job"}
      </div>
      {review.tags.length > 0 && (
        <div className="chip-list" style={{ gap: 4 }}>
          {review.tags.map((tag) => (
            <span key={tag} className="tag" style={{ fontSize: 11 }}>
              {TAG_LABEL[tag]}
            </span>
          ))}
        </div>
      )}
      {review.comment && <p style={{ fontSize: 14, lineHeight: 1.5 }}>{review.comment}</p>}
      {review.reply && (
        <div
          className="card card--compact"
          style={{ background: "var(--glass-subtle)", fontSize: 13, lineHeight: 1.5 }}
        >
          <strong>Reply: </strong>
          {review.reply}
        </div>
      )}
      {ownerWorkerId && <OwnerActions review={review} workerId={ownerWorkerId} />}
    </li>
  );
}

function OwnerActions({ review, workerId }: { review: PublicReview; workerId: string }) {
  const reply = useReplyToReview(workerId);
  const report = useReportReview();
  const [mode, setMode] = useState<"idle" | "reply" | "report">("idle");
  const [text, setText] = useState("");
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const value = text.trim();
    if (value === "") return;
    setError(null);
    try {
      if (mode === "reply") {
        await reply.mutateAsync({ reviewId: review.id, reply: value });
        setNotice("Your reply is posted under the review.");
      } else {
        await report.mutateAsync({ reviewId: review.id, reason: value });
        setNotice("Thanks. The Maritcho team will look at this review.");
      }
      setMode("idle");
      setText("");
    } catch (failure: unknown) {
      setError(failure instanceof Error ? failure.message : "That didn't go through.");
    }
  }

  if (mode === "idle") {
    return (
      <div className="stack" style={{ gap: 6 }}>
        <div className="row" style={{ gap: 8 }}>
          {review.reply === null && (
            <button
              type="button"
              className="btn btn--sm btn--soft"
              onClick={() => setMode("reply")}
            >
              <Icon name="chat" size={14} />
              Reply
            </button>
          )}
          <button
            type="button"
            className="btn btn--sm btn--ghost"
            onClick={() => setMode("report")}
          >
            Report
          </button>
        </div>
        {notice && (
          <p className="meta" role="status">
            {notice}
          </p>
        )}
      </div>
    );
  }

  const isReply = mode === "reply";
  return (
    <form className="stack" style={{ gap: 8 }} onSubmit={(event) => void submit(event)}>
      <label className="meta" htmlFor={`review-${review.id}-${mode}`}>
        {isReply
          ? "Your reply (shown publicly under the review, once)"
          : "What's wrong with this review? It stays up until the Maritcho team decides."}
      </label>
      <textarea
        id={`review-${review.id}-${mode}`}
        className="textarea"
        rows={2}
        maxLength={isReply ? 500 : 255}
        value={text}
        onChange={(event) => setText(event.target.value)}
      />
      {error && (
        <p className="field-error" role="alert">
          {error}
        </p>
      )}
      <div className="row" style={{ gap: 8 }}>
        <button
          type="submit"
          className="btn btn--sm"
          disabled={text.trim() === "" || reply.isPending || report.isPending}
        >
          {isReply ? "Post reply" : "Send report"}
        </button>
        <button type="button" className="btn btn--sm btn--ghost" onClick={() => setMode("idle")}>
          Cancel
        </button>
      </div>
    </form>
  );
}
