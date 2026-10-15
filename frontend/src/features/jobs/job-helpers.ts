import type { Job, JobStatus, MatchCandidate, MyJob } from "@/core/api/schemas";
import {
  distanceBandLabel,
  formatKm,
  formatMoney,
  formatPercent,
  gradeLabel,
} from "@/core/format/format";
import { tradeLabel } from "@/core/format/trades";

/** Jobs still collecting offers — the buyer reviews applicants. */
export function isOpenStatus(status: JobStatus): boolean {
  return status === "REQUESTED" || status === "MATCHED";
}

/** Where a buyer's job card should lead. */
export function employerJobHref(job: Pick<Job, "id" | "status">): string {
  return isOpenStatus(job.status) ? `/employer/jobs/${job.id}` : `/employer/jobs/${job.id}/track`;
}

/**
 * The backend does not store worker names, so a candidate is introduced
 * by what matters for the decision: their standing and trade.
 */
export function candidateTitle(
  candidate: Pick<MatchCandidate, "grade">,
  trade: Job["trade"],
): string {
  const role = tradeLabel(trade).toLowerCase();
  if (candidate.grade === "REGISTERED") return `New ${role}`;
  if (candidate.grade === "IDENTIFIED") return `ID-checked ${role}`;
  return `${gradeLabel(candidate.grade)} ${role}`;
}

export type CandidateSort = "best" | "closest" | "price";

export function sortCandidates(
  candidates: readonly MatchCandidate[],
  sort: CandidateSort,
): MatchCandidate[] {
  const copy = [...candidates];
  if (sort === "closest") {
    return copy.sort((a, b) => a.distance_km - b.distance_km);
  }
  if (sort === "price") {
    return copy.sort(
      (a, b) =>
        (a.quoted_amount ?? Number.POSITIVE_INFINITY) -
        (b.quoted_amount ?? Number.POSITIVE_INFINITY),
    );
  }
  // "best": server ranking, but people who actually offered come first.
  return copy.sort((a, b) => Number(b.quoted_amount !== null) - Number(a.quoted_amount !== null));
}

/**
 * inDrive-style: only workers who answered can be approved. Returns them
 * (in the chosen order) and how many more can see the job but haven't.
 */
export function splitResponders(
  candidates: readonly MatchCandidate[],
  sort: CandidateSort,
): { responded: MatchCandidate[]; waiting: number } {
  const responded = sortCandidates(
    candidates.filter((candidate) => candidate.quoted_amount !== null),
    sort,
  );
  return { responded, waiting: candidates.length - responded.length };
}

/** "Accepted your price" or "Offered $35" — what this worker said to the job. */
export function responseLabel(
  candidate: Pick<MatchCandidate, "quoted_amount">,
  budget: number | null,
): string | null {
  if (candidate.quoted_amount === null) return null;
  if (budget !== null && Math.abs(candidate.quoted_amount - budget) < 0.005) {
    return "Accepted your price";
  }
  return `Offered ${formatMoney(candidate.quoted_amount)}`;
}

/** Share of the agreed price held up-front; the on-site quote must exceed it. */
export const DEPOSIT_SHARE = 0.3;

export function depositFor(price: number | null): number {
  if (price === null || price <= 0) return 5;
  return Math.max(1, Math.round(price * DEPOSIT_SHARE));
}

/** Price the buyer is looking at for a candidate: their offer, else the budget. */
export function candidatePrice(
  candidate: MatchCandidate,
  job: Pick<Job, "budget_amount">,
): number | null {
  return candidate.quoted_amount ?? job.budget_amount;
}

export function activeJobs(jobs: readonly MyJob[]): MyJob[] {
  return jobs.filter((job) => job.status !== "COMPLETED" && job.status !== "CANCELLED");
}

export function finishedJobs(jobs: readonly MyJob[]): MyJob[] {
  return jobs.filter((job) => job.status === "COMPLETED");
}

export type TrackingStep = "Hired" | "Arrived" | "Working" | "Check & pay";

export const TRACKING_STEPS: readonly TrackingStep[] = [
  "Hired",
  "Arrived",
  "Working",
  "Check & pay",
];

/** Number of fully completed steps for a job status (design E6 stepper). */
export function completedSteps(status: JobStatus): number {
  switch (status) {
    case "BOOKED":
      return 1;
    case "IN_PROGRESS":
    case "DISPUTED":
      return 3;
    case "COMPLETED":
      return 4;
    default:
      return 0;
  }
}

/** One-line description for the sign-off record. */
export function summariseJob(job: Pick<Job, "trade" | "problem_description">): string {
  const description = (job.problem_description ?? "").split("\n")[0]?.trim() ?? "";
  const base = `${tradeLabel(job.trade)} job`;
  return description === "" ? base : `${base}: ${description}`.slice(0, 2000);
}

/** Folds the star rating and quick tags into the client's words on the immutable record. */
export function composeReview(
  stars: number,
  tags: readonly string[],
  note: string,
): string | undefined {
  const parts: string[] = [];
  if (stars > 0) parts.push(`${"★".repeat(stars)}${"☆".repeat(5 - stars)}`);
  if (tags.length > 0) parts.push(tags.join(", "));
  if (note.trim() !== "") parts.push(note.trim());
  const text = parts.join(" — ");
  return text === "" ? undefined : text.slice(0, 2000);
}

const NEEDED_PREFIX = "Needed: ";

/** Timing isn't a backend field yet, so it rides along in the description. */
export function withTiming(description: string, timing: string): string {
  return `${description.trim()}\n${NEEDED_PREFIX}${timing}`;
}

export function splitTiming(description: string | null): { text: string; timing: string | null } {
  if (description === null) return { text: "", timing: null };
  const lines = description.split("\n");
  const last = lines[lines.length - 1] ?? "";
  if (last.startsWith(NEEDED_PREFIX)) {
    return { text: lines.slice(0, -1).join("\n").trim(), timing: last.slice(NEEDED_PREFIX.length) };
  }
  return { text: description, timing: null };
}

/**
 * Plain-language "why we matched them", built from the structured fields.
 * The backend's `reason` string is an audit trail, not copy for people.
 */
export function matchExplanation(
  candidate: Pick<
    MatchCandidate,
    | "suburb"
    | "distance_band"
    | "distance_km"
    | "grade"
    | "jobs_completed"
    | "on_time_rate"
    | "dispute_rate"
  >,
  trade: Job["trade"],
): string {
  const where = `${distanceBandLabel(candidate.distance_band).toLowerCase()} — based in ${candidate.suburb}, ${formatKm(candidate.distance_km)} away`;
  const skill = `Registered for ${tradeLabel(trade).toLowerCase()} work`;
  if (candidate.jobs_completed === 0) {
    return `${skill}, ${where}. New on Maricho, so there's no track record yet.`;
  }
  return (
    `${skill}, ${where}. ${gradeLabel(candidate.grade)} with ${candidate.jobs_completed} ` +
    `${candidate.jobs_completed === 1 ? "job" : "jobs"} done: ${formatPercent(candidate.on_time_rate)} on time, ` +
    `${formatPercent(candidate.dispute_rate)} disputed.`
  );
}
