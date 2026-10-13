"use client";

import { Icon } from "@/components/ui/Icon";

export const REVIEW_TAGS = [
  "On time",
  "Quality work",
  "Cleaned up",
  "Fair price",
  "Polite",
] as const;

export interface ReviewDraft {
  stars: number;
  tags: readonly string[];
  note: string;
}

type Props = { value: ReviewDraft; onChange: (next: ReviewDraft) => void };

/** "How did they do?" — stored on the job's sign-off record as a reference. */
export function ReviewPanel({ value, onChange }: Props) {
  function toggleTag(tag: string): void {
    const tags = value.tags.includes(tag)
      ? value.tags.filter((item) => item !== tag)
      : [...value.tags, tag];
    onChange({ ...value, tags });
  }

  return (
    <section className="card" aria-labelledby="review-heading">
      <h2 id="review-heading" style={{ fontSize: 16, fontWeight: 700 }}>
        How did they do?
      </h2>
      <p className="meta meta--secondary" style={{ marginTop: 4, lineHeight: 1.5 }}>
        Your review is saved on the job record — it helps the next person decide.
      </p>
      <div className="stars" role="radiogroup" aria-label="Rating" style={{ marginTop: 12 }}>
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            role="radio"
            aria-checked={value.stars === star}
            aria-label={`${star} ${star === 1 ? "star" : "stars"}`}
            className={star <= value.stars ? "star-btn star-btn--lit" : "star-btn"}
            onClick={() => onChange({ ...value, stars: star })}
          >
            <Icon name="star" size={22} filled />
          </button>
        ))}
      </div>
      <div className="chip-list" style={{ marginTop: 12, gap: 6 }}>
        {REVIEW_TAGS.map((tag) => (
          <button
            key={tag}
            type="button"
            className="chip chip--sm chip--soft"
            aria-pressed={value.tags.includes(tag)}
            onClick={() => toggleTag(tag)}
          >
            {tag}
          </button>
        ))}
      </div>
      <label htmlFor="jt-note" className="visually-hidden">
        Add a few words
      </label>
      <textarea
        id="jt-note"
        rows={2}
        className="textarea"
        style={{ marginTop: 12 }}
        placeholder="Add a few words (optional)"
        maxLength={500}
        value={value.note}
        onChange={(event) => onChange({ ...value, note: event.target.value })}
      />
    </section>
  );
}
