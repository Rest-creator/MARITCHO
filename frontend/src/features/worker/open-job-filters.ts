import type { OpenJob, Trade } from "@/core/api/schemas";
import { splitTiming } from "@/features/jobs/job-helpers";

export type JobFilter = { kind: "all" } | { kind: "today" } | { kind: "trade"; trade: Trade };

/** Jobs within the worker's travel radius, closest first. */
export function jobsWithinReach(jobs: readonly OpenJob[], travelKm: number): OpenJob[] {
  return jobs
    .filter((job) => job.distance_km <= travelKm)
    .sort((a, b) => a.distance_km - b.distance_km);
}

export function applyJobFilter(jobs: readonly OpenJob[], filter: JobFilter): OpenJob[] {
  switch (filter.kind) {
    case "today":
      return jobs.filter((job) => splitTiming(job.problem_description).timing === "Today");
    case "trade":
      return jobs.filter((job) => job.trade === filter.trade);
    default:
      return [...jobs];
  }
}

export function isSameFilter(a: JobFilter, b: JobFilter): boolean {
  if (a.kind !== b.kind) return false;
  return a.kind !== "trade" || (b.kind === "trade" && a.trade === b.trade);
}

/** A job ranked for this worker, with the plain-language reasons it ranks there. */
export interface RankedJob {
  job: OpenJob;
  score: number;
  reasons: string[];
}

/**
 * "Jobs near you" order: the backend already keeps only jobs in the
 * worker's skills; this puts the best ones for them first — close, needed
 * soon, freshly posted, with a price they can accept in one tap — and
 * moves jobs they've already answered to the bottom.
 */
export function rankOpenJobs(
  jobs: readonly OpenJob[],
  answeredJobIds: ReadonlySet<string>,
  now: Date = new Date(),
): RankedJob[] {
  return jobs
    .map((job) => {
      const reasons: string[] = [];
      let score = Math.max(0, 10 - job.distance_km) * 3;
      if (job.distance_km < 1) reasons.push("close by");

      const timing = splitTiming(job.problem_description).timing;
      if (timing === "Today") {
        score += 20;
        reasons.push("needed today");
      } else if (timing === "This week") {
        score += 8;
      }

      if (job.created_at !== null) {
        const hoursOld = (now.getTime() - new Date(job.created_at).getTime()) / 3_600_000;
        if (hoursOld <= 1) {
          score += 15;
          reasons.push("just posted");
        } else if (hoursOld <= 6) {
          score += 8;
        } else if (hoursOld <= 24) {
          score += 3;
        }
      }

      if (job.budget_amount !== null) score += 5;
      if (answeredJobIds.has(job.job_id)) score -= 100;
      return { job, score, reasons };
    })
    .sort((a, b) => b.score - a.score);
}
