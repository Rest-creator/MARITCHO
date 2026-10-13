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
