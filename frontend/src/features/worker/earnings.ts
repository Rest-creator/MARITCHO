import type { Job } from "@/core/api/schemas";

export interface MonthSummary {
  earned: number;
  jobsDone: number;
}

/** Signed-off jobs this calendar month and what they paid. */
export function summariseMonth(jobs: readonly Job[], now: Date = new Date()): MonthSummary {
  const done = jobs.filter((job) => {
    if (job.status !== "COMPLETED") return false;
    const finished = new Date(job.updated_at);
    return finished.getFullYear() === now.getFullYear() && finished.getMonth() === now.getMonth();
  });
  return {
    earned: done.reduce((sum, job) => sum + (job.quote_amount ?? 0), 0),
    jobsDone: done.length,
  };
}

export function monthLabel(now: Date = new Date()): string {
  return `${now.toLocaleDateString("en-GB", { month: "long" })} so far`;
}
