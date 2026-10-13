"use client";

import { useState } from "react";
import Link from "next/link";

import { Avatar } from "@/components/ui/Avatar";
import { BackButton } from "@/components/ui/BackButton";
import { Icon } from "@/components/ui/Icon";
import { Screen } from "@/components/ui/Screen";
import { ErrorState, Skeleton } from "@/components/ui/States";
import type { Job } from "@/core/api/schemas";
import { formatMoney, formatRelativeTime, formatShortDate } from "@/core/format/format";
import { tradeLabel } from "@/core/format/trades";
import { DisputeSheet } from "@/features/jobs/DisputeSheet";
import { useCompleteJob, useJob, useRecord } from "@/features/jobs/hooks";
import {
  TRACKING_STEPS,
  completedSteps,
  composeReview,
  splitTiming,
  summariseJob,
} from "@/features/jobs/job-helpers";
import { ReviewPanel, type ReviewDraft } from "@/features/jobs/ReviewPanel";

type Props = { jobId: string };

function Stepper({ job }: { job: Job }) {
  const done = completedSteps(job.status);
  return (
    <ol className="stepper" aria-label="Job progress">
      {TRACKING_STEPS.map((step, index) => {
        const state = index < done ? "done" : index === done ? "current" : "todo";
        return (
          <li
            key={step}
            className={`stepper__step ${state === "done" ? "stepper__step--done" : ""} ${state === "current" ? "stepper__step--current" : ""}`}
            aria-current={state === "current" ? "step" : undefined}
          >
            <span className="stepper__bar" />
            {step}
          </li>
        );
      })}
    </ol>
  );
}

function statusCopy(job: Job): { title: string; detail: string } {
  switch (job.status) {
    case "BOOKED":
      return {
        title: "Your worker is on the way",
        detail: "They'll confirm the full price once they see the job.",
      };
    case "IN_PROGRESS":
      return {
        title: `Price confirmed: ${formatMoney(job.quote_amount)}`,
        detail:
          job.labor_amount !== null
            ? `Labour ${formatMoney(job.labor_amount)} + materials ${formatMoney(job.materials_amount ?? 0)} · ${formatRelativeTime(job.updated_at)}`
            : `Updated ${formatRelativeTime(job.updated_at)}`,
      };
    case "DISPUTED":
      return {
        title: "Payment is on hold",
        detail: "The worker has been asked to respond. Usually they come back and fix it.",
      };
    case "COMPLETED":
      return { title: "Job signed off", detail: `Paid · ${formatShortDate(job.updated_at)}` };
    default:
      return { title: "Waiting", detail: "" };
  }
}

/** Design E6 · Job progress, confirm & review. */
export function JobTrackingScreen({ jobId }: Props) {
  const job = useJob(jobId);
  const completeJob = useCompleteJob();
  const record = useRecord(jobId, job.data?.status === "COMPLETED");
  const [review, setReview] = useState<ReviewDraft>({ stars: 5, tags: [], note: "" });
  const [isDisputeOpen, setIsDisputeOpen] = useState(false);

  if (job.isPending) {
    return (
      <Screen>
        <Skeleton height={56} />
        <Skeleton height={180} count={2} />
      </Screen>
    );
  }
  if (!job.data) {
    return (
      <Screen>
        <div className="topbar">
          <BackButton fallbackHref="/employer/jobs" />
        </div>
        <ErrorState
          message={job.error?.message ?? "We couldn't load this job."}
          onRetry={() => void job.refetch()}
        />
      </Screen>
    );
  }

  const data = job.data;
  const heading =
    splitTiming(data.problem_description).text.split("\n")[0] || tradeLabel(data.trade);
  const copy = statusCopy(data);
  const canSignOff = data.status === "IN_PROGRESS";
  const price = data.quote_amount;
  const workerName = `${tradeLabel(data.trade)}`;

  function handleConfirm(): void {
    completeJob.mutate({
      jobId,
      what_was_done: summariseJob(data),
      client_words: composeReview(review.stars, review.tags, review.note),
    });
  }

  return (
    <Screen>
      <div className="topbar">
        <BackButton fallbackHref="/employer/jobs" />
        <div className="topbar__text">
          <h1 className="title truncate">{heading}</h1>
          <div className="meta">
            Hired {workerName.toLowerCase()}
            {price === null ? "" : ` · ${formatMoney(price)}`}
          </div>
        </div>
      </div>

      <section className="card">
        <Stepper job={data} />
        <div className="row" style={{ marginTop: 14 }}>
          <Avatar name={workerName} seed={data.worker_id ?? data.id} />
          <div className="grow">
            <div style={{ fontSize: 14, fontWeight: 700 }}>{copy.title}</div>
            <div className="meta">{copy.detail}</div>
          </div>
        </div>
        <div className="card__divider row row--between">
          <span className="meta meta--secondary truncate">
            {data.address}, {data.suburb}
          </span>
          <Link href={`/chat/${data.id}`} className="btn btn--sm" style={{ height: 36 }}>
            <Icon name="chat" size={16} />
            Message
          </Link>
        </div>
      </section>

      {data.status === "COMPLETED" && (
        <section className="card card--emerald">
          <div className="row row--tight text-emerald" style={{ fontSize: 12, fontWeight: 700 }}>
            <Icon name="shieldCheck" size={16} />
            Confirmed through Maricho
          </div>
          <p style={{ marginTop: 8, fontSize: 14, lineHeight: 1.5 }}>
            {record.data?.what_was_done ?? summariseJob(data)}
          </p>
          {record.data?.client_words && (
            <p
              className="meta meta--secondary"
              style={{ marginTop: 6, fontSize: 13, lineHeight: 1.5 }}
            >
              “{record.data.client_words}”
            </p>
          )}
          <Link
            href={`/employer/post?trade=${data.trade}`}
            className="btn btn--soft btn--block"
            style={{ marginTop: 12 }}
          >
            Hire again
          </Link>
        </section>
      )}

      {canSignOff && <ReviewPanel value={review} onChange={setReview} />}

      {data.status === "BOOKED" && (
        <div className="banner banner--quiet">
          <Icon name="clock" size={18} />
          You can confirm and pay once they&apos;ve priced the job on site.
        </div>
      )}

      <div className="spacer" />

      {canSignOff && (
        <>
          <div className="row row--tight meta" style={{ justifyContent: "center" }}>
            <Icon name="shield" size={14} />
            Pay by EcoCash or cash
          </div>
          {completeJob.error && (
            <p className="field-error" role="alert">
              {completeJob.error.message}
            </p>
          )}
          <button
            type="button"
            className="btn btn--primary btn--cta"
            disabled={completeJob.isPending}
            onClick={handleConfirm}
          >
            {completeJob.isPending ? "Confirming…" : `Confirm job done & pay ${formatMoney(price)}`}
          </button>
          <button type="button" className="btn btn--ghost" onClick={() => setIsDisputeOpen(true)}>
            Something&apos;s not right
          </button>
        </>
      )}

      {isDisputeOpen && <DisputeSheet jobId={jobId} onClose={() => setIsDisputeOpen(false)} />}
    </Screen>
  );
}
