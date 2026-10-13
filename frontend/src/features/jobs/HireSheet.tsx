"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Sheet } from "@/components/ui/Sheet";
import type { Job, MatchCandidate } from "@/core/api/schemas";
import { formatMoney } from "@/core/format/format";
import { useBookJob } from "@/features/jobs/hooks";
import { candidatePrice, candidateTitle, depositFor } from "@/features/jobs/job-helpers";

type Currency = "USD" | "ECOCASH";

type Props = { job: Job; candidate: MatchCandidate; onClose: () => void };

/** Confirms the hire and the deposit held until the buyer signs the job off. */
export function HireSheet({ job, candidate, onClose }: Props) {
  const router = useRouter();
  const bookJob = useBookJob();
  const [currency, setCurrency] = useState<Currency>("USD");
  const price = candidatePrice(candidate, job);
  const deposit = depositFor(price);
  const title = candidateTitle(candidate, job.trade);

  function handleHire(): void {
    bookJob.mutate(
      { jobId: job.id, worker_id: candidate.worker_id, deposit_amount: deposit, currency },
      { onSuccess: () => router.replace(`/employer/jobs/${job.id}/track`) },
    );
  }

  return (
    <Sheet
      title={`Hire this ${title.toLowerCase()}?`}
      isOpen
      onClose={onClose}
      isFitContent
      footer={
        <button
          type="button"
          className="btn btn--primary btn--cta"
          disabled={bookJob.isPending}
          onClick={handleHire}
        >
          {bookJob.isPending ? "Hiring…" : `Hire · hold ${formatMoney(deposit)} deposit`}
        </button>
      }
    >
      <div className="card card--quiet stack">
        <div className="row row--between">
          <span className="meta meta--secondary">Their price</span>
          <span className="strong">{price === null ? "Agreed on site" : formatMoney(price)}</span>
        </div>
        <div className="row row--between">
          <span className="meta meta--secondary">Deposit held now</span>
          <span className="strong text-amber">{formatMoney(deposit)}</span>
        </div>
        <p className="meta" style={{ lineHeight: 1.5 }}>
          Maricho holds the deposit. The worker confirms the full price when they see the job, and
          you only release payment once you&apos;re happy it&apos;s done.
        </p>
      </div>
      <div className="segmented segmented--choice" role="group" aria-label="Pay with">
        <button
          type="button"
          className="segmented__tab"
          aria-pressed={currency === "USD"}
          onClick={() => setCurrency("USD")}
        >
          Cash (USD)
        </button>
        <button
          type="button"
          className="segmented__tab"
          aria-pressed={currency === "ECOCASH"}
          onClick={() => setCurrency("ECOCASH")}
        >
          EcoCash
        </button>
      </div>
      {bookJob.error && (
        <p className="field-error" role="alert">
          {bookJob.error.message}
        </p>
      )}
    </Sheet>
  );
}
