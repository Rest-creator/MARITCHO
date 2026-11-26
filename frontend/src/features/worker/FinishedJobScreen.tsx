"use client";

import { BackButton } from "@/components/ui/BackButton";
import { Icon } from "@/components/ui/Icon";
import { Screen } from "@/components/ui/Screen";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/States";
import { formatMoney, formatShortDate } from "@/core/format/format";
import { tradeLabel } from "@/core/format/trades";
import { useAssignedJobs } from "@/features/jobs/hooks";
import { splitTiming } from "@/features/jobs/job-helpers";
import { JobReviewCard } from "@/features/reviews/JobReviewCard";

type Props = { jobId: string };

/** A signed-off job from the worker's side: what was done, and rating the client (ADR-011). */
export function FinishedJobScreen({ jobId }: Props) {
  const assigned = useAssignedJobs();
  const job = assigned.data?.find((item) => item.id === jobId);

  if (assigned.isPending) {
    return (
      <Screen glow="worker">
        <Skeleton height={56} />
        <Skeleton height={160} count={2} />
      </Screen>
    );
  }

  if (!job || job.status !== "COMPLETED") {
    return (
      <Screen glow="worker">
        <div className="topbar">
          <BackButton fallbackHref="/worker/work?tab=done" />
        </div>
        {assigned.isError ? (
          <ErrorState message={assigned.error.message} onRetry={() => void assigned.refetch()} />
        ) : (
          <EmptyState title="This job isn't in your finished work" icon="briefcase">
            Only signed-off jobs can be reviewed.
          </EmptyState>
        )}
      </Screen>
    );
  }

  const title = splitTiming(job.problem_description).text.split("\n")[0] || tradeLabel(job.trade);

  return (
    <Screen glow="worker">
      <div className="topbar">
        <BackButton fallbackHref="/worker/work?tab=done" />
        <div className="topbar__text">
          <h1 className="title">{title}</h1>
          <div className="meta">
            {job.suburb} · signed off {formatShortDate(job.updated_at)}
          </div>
        </div>
      </div>

      <section className="card card--emerald row" style={{ gap: 10, alignItems: "center" }}>
        <Icon name="shieldCheck" size={18} />
        <span className="grow">Signed off through Maritcho</span>
        <strong>{formatMoney(job.quote_amount)}</strong>
      </section>

      <JobReviewCard jobId={jobId} otherName="the client" />
    </Screen>
  );
}
