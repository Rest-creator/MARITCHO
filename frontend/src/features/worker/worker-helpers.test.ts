import { describe, expect, it } from "vitest";

import type { Job, OpenJob } from "@/core/api/schemas";
import { monthLabel, summariseMonth } from "@/features/worker/earnings";
import { parseOfferAmount } from "@/features/worker/money-input";
import {
  applyJobFilter,
  isSameFilter,
  jobsWithinReach,
  rankOpenJobs,
} from "@/features/worker/open-job-filters";

function openJob(overrides: Partial<OpenJob>): OpenJob {
  return {
    job_id: "j",
    trade: "WELDING",
    suburb: "Avondale",
    budget_amount: 30,
    problem_description: "Gate\nNeeded: Today",
    created_at: "2026-10-13T10:00:00Z",
    distance_band: "NEARBY",
    distance_km: 3,
    ...overrides,
  };
}

function assigned(overrides: Partial<Job>): Job {
  return {
    id: "a",
    buyer_id: "b",
    worker_id: "w",
    status: "COMPLETED",
    trade: "WELDING",
    suburb: "Avondale",
    address: "22 Ridge Rd",
    landmark_narrative: null,
    latitude: null,
    longitude: null,
    problem_description: null,
    problem_photo_url: null,
    budget_amount: null,
    currency: "USD",
    labor_amount: 30,
    materials_amount: 5,
    quote_amount: 35,
    created_at: "2026-10-01T10:00:00Z",
    updated_at: "2026-10-05T10:00:00Z",
    ...overrides,
  };
}

describe("open job filters", () => {
  const jobs = [
    openJob({ job_id: "far", distance_km: 14 }),
    openJob({
      job_id: "fence",
      trade: "BUILDING",
      distance_km: 6,
      problem_description: "Fence\nNeeded: This week",
    }),
    openJob({ job_id: "near", distance_km: 1 }),
  ];

  it("keeps jobs within the travel radius, closest first", () => {
    expect(jobsWithinReach(jobs, 10).map((job) => job.job_id)).toEqual(["near", "fence"]);
  });

  it("filters by trade and by today", () => {
    expect(applyJobFilter(jobs, { kind: "trade", trade: "BUILDING" }).map((j) => j.job_id)).toEqual(
      ["fence"],
    );
    expect(applyJobFilter(jobs, { kind: "today" }).map((j) => j.job_id)).toEqual(["far", "near"]);
    expect(applyJobFilter(jobs, { kind: "all" })).toHaveLength(3);
  });

  it("compares filters by value", () => {
    expect(isSameFilter({ kind: "all" }, { kind: "all" })).toBe(true);
    expect(isSameFilter({ kind: "trade", trade: "SOLAR" }, { kind: "trade", trade: "SOLAR" })).toBe(
      true,
    );
    expect(
      isSameFilter({ kind: "trade", trade: "SOLAR" }, { kind: "trade", trade: "WELDING" }),
    ).toBe(false);
    expect(isSameFilter({ kind: "today" }, { kind: "all" })).toBe(false);
  });
});

describe("summariseMonth", () => {
  it("sums signed-off jobs in the current month only", () => {
    const now = new Date("2026-10-20T12:00:00Z");
    const summary = summariseMonth(
      [
        assigned({ id: "1", quote_amount: 35 }),
        assigned({ id: "2", quote_amount: 120, updated_at: "2026-10-18T09:00:00Z" }),
        assigned({ id: "3", quote_amount: 50, updated_at: "2026-09-28T09:00:00Z" }),
        assigned({ id: "4", status: "IN_PROGRESS", quote_amount: 80 }),
      ],
      now,
    );
    expect(summary).toEqual({ earned: 155, jobsDone: 2 });
    expect(monthLabel(now)).toBe("October so far");
  });
});

describe("parseOfferAmount", () => {
  it.each([
    ["35", 35],
    ["35.555", 35.56],
    ["0", null],
    ["", null],
    ["abc", null],
    ["-3", null],
  ])("%s → %s", (raw, expected) => {
    expect(parseOfferAmount(raw)).toBe(expected);
  });
});

describe("rankOpenJobs", () => {
  const now = new Date("2026-10-13T10:30:00Z");

  it("puts close, urgent, fresh jobs first and says why", () => {
    const ranked = rankOpenJobs(
      [
        openJob({
          job_id: "far-old",
          distance_km: 8,
          problem_description: "Gate",
          created_at: "2026-10-10T10:00:00Z",
        }),
        openJob({ job_id: "near-today-new", distance_km: 0.5, created_at: "2026-10-13T10:10:00Z" }),
        openJob({ job_id: "mid", distance_km: 3, problem_description: "Gate\nNeeded: This week" }),
      ],
      new Set(),
      now,
    );
    expect(ranked.map((entry) => entry.job.job_id)).toEqual(["near-today-new", "mid", "far-old"]);
    expect(ranked[0]?.reasons).toEqual(["close by", "needed today", "just posted"]);
  });

  it("moves jobs the worker already answered to the bottom", () => {
    const ranked = rankOpenJobs(
      [
        openJob({ job_id: "answered", distance_km: 0.2 }),
        openJob({ job_id: "new", distance_km: 6 }),
      ],
      new Set(["answered"]),
      now,
    );
    expect(ranked.map((entry) => entry.job.job_id)).toEqual(["new", "answered"]);
  });
});
