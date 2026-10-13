"use client";

import { useState } from "react";
import Link from "next/link";

import { Screen } from "@/components/ui/Screen";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/States";
import type { MyJob } from "@/core/api/schemas";
import { EmployerJobCard } from "@/features/employer/EmployerJobCard";
import { EmployerTabBar } from "@/features/employer/EmployerTabBar";
import { useMyJobs } from "@/features/jobs/hooks";
import { isOpenStatus } from "@/features/jobs/job-helpers";

type Tab = "open" | "active" | "done";

const FILTERS: Record<Tab, (job: MyJob) => boolean> = {
  open: (job) => isOpenStatus(job.status),
  active: (job) => ["BOOKED", "IN_PROGRESS", "DISPUTED"].includes(job.status),
  done: (job) => job.status === "COMPLETED" || job.status === "CANCELLED",
};

/** "My jobs" tab — every job the employer has posted, by stage. */
export function MyJobsScreen() {
  const jobs = useMyJobs();
  const [tab, setTab] = useState<Tab>("open");
  const all = jobs.data ?? [];
  const count = (key: Tab): number => all.filter(FILTERS[key]).length;
  const visible = all.filter(FILTERS[tab]);

  return (
    <Screen hasTabBar>
      <h1 className="title title--page">My jobs</h1>
      <div className="segmented" role="tablist" aria-label="Job stage">
        {(
          [
            ["open", `Open (${count("open")})`],
            ["active", `Active (${count("active")})`],
            ["done", "Done"],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            type="button"
            role="tab"
            aria-selected={tab === key}
            className="segmented__tab"
            onClick={() => setTab(key)}
          >
            {label}
          </button>
        ))}
      </div>

      {jobs.isPending && <Skeleton height={110} count={3} />}
      {jobs.isError && !jobs.data && (
        <ErrorState message={jobs.error.message} onRetry={() => void jobs.refetch()} />
      )}
      {jobs.data && visible.length === 0 && (
        <EmptyState
          title={tab === "done" ? "Nothing finished yet" : "No jobs here"}
          icon="briefcase"
          action={
            <Link href="/employer/post" className="btn btn--primary btn--sm">
              Post a job
            </Link>
          }
        />
      )}
      <div className="stack">
        {visible.map((job) => (
          <EmployerJobCard key={job.id} job={job} />
        ))}
      </div>
      <EmployerTabBar />
    </Screen>
  );
}
