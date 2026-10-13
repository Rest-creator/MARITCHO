"use client";

import { useState } from "react";
import Link from "next/link";

import { Icon } from "@/components/ui/Icon";
import type { Job } from "@/core/api/schemas";
import { formatMoney } from "@/core/format/format";
import { tradeLabel } from "@/core/format/trades";
import { splitTiming } from "@/features/jobs/job-helpers";
import { QuoteSheet } from "@/features/worker/QuoteSheet";
import { RespondSheet } from "@/features/worker/RespondSheet";

type Props = { job: Job; offeredAmount: number | null };

function directionsUrl(job: Job): string {
  if (job.latitude !== null && job.longitude !== null) {
    return `https://www.google.com/maps/dir/?api=1&destination=${job.latitude},${job.longitude}`;
  }
  const query = encodeURIComponent(`${job.address}, ${job.suburb}, Harare`);
  return `https://www.google.com/maps/search/?api=1&query=${query}`;
}

/** A hired job on W4 — get there, talk, then confirm the price on site. */
export function ActiveJobCard({ job, offeredAmount }: Props) {
  const [sheet, setSheet] = useState<"quote" | "respond" | null>(null);
  const { text, timing } = splitTiming(job.problem_description);
  const title = text.split("\n")[0] || tradeLabel(job.trade);
  const price = job.quote_amount ?? offeredAmount ?? job.budget_amount;

  const badge =
    job.status === "BOOKED"
      ? { label: "You got the job", tone: "badge--emerald" }
      : job.status === "IN_PROGRESS"
        ? { label: "Price agreed · working", tone: "badge--emerald" }
        : { label: "Concern raised", tone: "badge--danger" };

  return (
    <article className="card card--emerald">
      <div className="row row--between">
        <span className={`badge ${badge.tone}`}>{badge.label}</span>
        <span style={{ fontSize: 16, fontWeight: 700 }}>{formatMoney(price)}</span>
      </div>
      <h3 style={{ marginTop: 10, fontSize: 16, fontWeight: 700 }}>{title}</h3>
      <div className="meta meta--secondary" style={{ marginTop: 4, fontSize: 13 }}>
        {job.address}, {job.suburb}
      </div>
      {job.landmark_narrative && (
        <div className="meta" style={{ marginTop: 2 }}>
          {job.landmark_narrative}
        </div>
      )}

      {job.status === "BOOKED" && timing && (
        <div className="banner banner--amber" style={{ marginTop: 10, padding: "10px 12px" }}>
          <Icon name="clock" size={18} />
          Needed {timing.toLowerCase() === "today" ? "today" : timing}
        </div>
      )}
      {job.status === "IN_PROGRESS" && (
        <div className="banner banner--quiet" style={{ marginTop: 10 }}>
          <Icon name="check" size={16} />
          When you&apos;re done, the client checks the work and releases payment.
        </div>
      )}

      <div className="btn-grid btn-grid--three" style={{ marginTop: 12 }}>
        <a
          href={directionsUrl(job)}
          target="_blank"
          rel="noopener noreferrer"
          className="btn btn--sm"
        >
          Directions
        </a>
        <Link href={`/chat/${job.id}`} className="btn btn--sm">
          Message
        </Link>
        {job.status === "BOOKED" && (
          <button
            type="button"
            className="btn btn--primary btn--sm"
            onClick={() => setSheet("quote")}
          >
            I&apos;ve arrived
          </button>
        )}
        {job.status === "DISPUTED" && (
          <button
            type="button"
            className="btn btn--primary btn--sm"
            onClick={() => setSheet("respond")}
          >
            Respond
          </button>
        )}
        {job.status === "IN_PROGRESS" && (
          <span className="btn btn--sm" aria-disabled="true">
            Working
          </span>
        )}
      </div>

      {sheet === "quote" && (
        <QuoteSheet job={job} offeredAmount={offeredAmount} onClose={() => setSheet(null)} />
      )}
      {sheet === "respond" && <RespondSheet jobId={job.id} onClose={() => setSheet(null)} />}
    </article>
  );
}
