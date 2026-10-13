"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { BackButton } from "@/components/ui/BackButton";
import { Icon } from "@/components/ui/Icon";
import { Screen } from "@/components/ui/Screen";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/States";
import type { MatchCandidate } from "@/core/api/schemas";
import { formatMoney } from "@/core/format/format";
import { tradeLabel } from "@/core/format/trades";
import { CandidateCard } from "@/features/jobs/CandidateCard";
import { HireSheet } from "@/features/jobs/HireSheet";
import { useJob, useMatches } from "@/features/jobs/hooks";
import {
  isOpenStatus,
  sortCandidates,
  splitTiming,
  type CandidateSort,
} from "@/features/jobs/job-helpers";

const SORTS: readonly { id: CandidateSort; label: string }[] = [
  { id: "best", label: "Best match" },
  { id: "closest", label: "Closest" },
  { id: "price", label: "Lowest price" },
];

type Props = { jobId: string };

/** Design E4 · People who offered to help. */
export function ApplicantsScreen({ jobId }: Props) {
  const router = useRouter();
  const job = useJob(jobId);
  const isOpen = job.data ? isOpenStatus(job.data.status) : false;
  const matches = useMatches(jobId, isOpen);
  const [sort, setSort] = useState<CandidateSort>("best");
  const [hiring, setHiring] = useState<MatchCandidate | null>(null);

  useEffect(() => {
    if (job.data && !isOpenStatus(job.data.status)) {
      router.replace(`/employer/jobs/${jobId}/track`);
    }
  }, [job.data, jobId, router]);

  const candidates = sortCandidates(matches.data ?? [], sort);
  const offers = candidates.filter((candidate) => candidate.quoted_amount !== null).length;
  const timing = job.data ? splitTiming(job.data.problem_description).timing : null;
  const subtitle = job.data
    ? [
        tradeLabel(job.data.trade),
        job.data.suburb,
        timing,
        job.data.budget_amount === null ? null : `US${formatMoney(job.data.budget_amount)}`,
      ]
        .filter(Boolean)
        .join(" · ")
    : "";
  const heading = job.data
    ? splitTiming(job.data.problem_description).text.split("\n")[0] || tradeLabel(job.data.trade)
    : "Your job";

  return (
    <Screen>
      <div className="topbar">
        <BackButton fallbackHref="/employer" />
        <div className="topbar__text">
          <h1 className="title truncate">{heading}</h1>
          <div className="meta truncate">{subtitle}</div>
        </div>
      </div>

      {job.isError && !job.data && (
        <ErrorState message={job.error.message} onRetry={() => void job.refetch()} />
      )}
      {(job.isPending || (isOpen && matches.isPending)) && <Skeleton height={150} count={3} />}
      {matches.isError && !matches.data && (
        <ErrorState message={matches.error.message} onRetry={() => void matches.refetch()} />
      )}

      {matches.data && candidates.length > 0 && job.data && (
        <>
          <div className="banner banner--emerald">
            <span className="text-emerald" style={{ display: "flex" }}>
              <Icon name="shieldCheck" size={20} />
            </span>
            <span>
              {offers > 0
                ? `${offers} ${offers === 1 ? "person has" : "people have"} offered to help. `
                : "These checked workers can do this job. "}
              Each one&apos;s skills and track record have been checked.
            </span>
          </div>
          <div className="chip-list chip-list--scroll" role="group" aria-label="Sort offers">
            {SORTS.map((option) => (
              <button
                key={option.id}
                type="button"
                className="filter-chip"
                aria-pressed={sort === option.id}
                onClick={() => setSort(option.id)}
              >
                {option.label}
              </button>
            ))}
          </div>
          {candidates.map((candidate, index) => (
            <CandidateCard
              key={candidate.worker_id}
              job={job.data}
              candidate={candidate}
              isTopPick={index === 0}
              onHire={setHiring}
            />
          ))}
        </>
      )}

      {matches.data && candidates.length === 0 && (
        <EmptyState
          title="Looking for people nearby"
          icon="clock"
          action={
            <button
              type="button"
              className="btn btn--sm"
              onClick={() => void matches.refetch()}
              disabled={matches.isFetching}
            >
              {matches.isFetching ? "Checking…" : "Check again"}
            </button>
          }
        >
          No checked workers have offered yet. Workers nearby can see your job and offer to help.
        </EmptyState>
      )}

      {hiring && job.data && (
        <HireSheet job={job.data} candidate={hiring} onClose={() => setHiring(null)} />
      )}
    </Screen>
  );
}
