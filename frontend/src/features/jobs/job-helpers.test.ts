import { describe, expect, it } from "vitest";

import type { MatchCandidate, MyJob } from "@/core/api/schemas";
import {
  activeJobs,
  candidatePrice,
  candidateTitle,
  completedSteps,
  composeReview,
  depositFor,
  employerJobHref,
  finishedJobs,
  isOpenStatus,
  matchExplanation,
  responseLabel,
  sortCandidates,
  splitResponders,
  splitTiming,
  summariseJob,
  withTiming,
} from "@/features/jobs/job-helpers";

function candidate(overrides: Partial<MatchCandidate>): MatchCandidate {
  return {
    worker_id: "w1",
    suburb: "Avondale",
    travel_means: null,
    distance_band: "NEARBY",
    distance_km: 3,
    grade: "JOURNEYMAN",
    on_time_rate: 90,
    dispute_rate: 0,
    fill_rate: 95,
    jobs_completed: 10,
    reason: "Skilled in plumbing",
    quoted_amount: null,
    availability_note: null,
    quoted_at: null,
    ...overrides,
  };
}

function job(overrides: Partial<MyJob>): MyJob {
  return {
    id: "j1",
    buyer_id: "b1",
    worker_id: null,
    status: "REQUESTED",
    trade: "PLUMBING",
    suburb: "Borrowdale",
    address: "14 Harrow Rd",
    landmark_narrative: null,
    latitude: null,
    longitude: null,
    problem_description: "Leaking pipe",
    problem_photo_url: null,
    budget_amount: 30,
    currency: null,
    labor_amount: null,
    materials_amount: null,
    quote_amount: null,
    created_at: "2026-10-13T10:00:00Z",
    updated_at: "2026-10-13T10:00:00Z",
    offer_count: 0,
    ...overrides,
  };
}

describe("job routing", () => {
  it("sends open jobs to applicants and the rest to tracking", () => {
    expect(isOpenStatus("REQUESTED")).toBe(true);
    expect(isOpenStatus("MATCHED")).toBe(true);
    expect(isOpenStatus("BOOKED")).toBe(false);
    expect(employerJobHref({ id: "j1", status: "MATCHED" })).toBe("/employer/jobs/j1");
    expect(employerJobHref({ id: "j1", status: "BOOKED" })).toBe("/employer/jobs/j1/track");
  });

  it("splits active and finished jobs", () => {
    const jobs = [
      job({ id: "a", status: "BOOKED" }),
      job({ id: "b", status: "COMPLETED" }),
      job({ id: "c", status: "CANCELLED" }),
    ];
    expect(activeJobs(jobs).map((j) => j.id)).toEqual(["a"]);
    expect(finishedJobs(jobs).map((j) => j.id)).toEqual(["b"]);
  });
});

describe("candidates", () => {
  it("introduces workers by standing and trade", () => {
    expect(candidateTitle({ grade: "EXPERT" }, "PLUMBING")).toBe("Expert plumber");
    expect(candidateTitle({ grade: "REGISTERED" }, "WELDING")).toBe("New welder");
    expect(candidateTitle({ grade: "IDENTIFIED" }, "SOLAR")).toBe("ID-checked solar installer");
  });

  const list = [
    candidate({ worker_id: "far", distance_km: 9, quoted_amount: 20 }),
    candidate({ worker_id: "noquote", distance_km: 1 }),
    candidate({ worker_id: "pricey", distance_km: 4, quoted_amount: 40 }),
  ];

  it("sorts by distance", () => {
    expect(sortCandidates(list, "closest").map((c) => c.worker_id)).toEqual([
      "noquote",
      "pricey",
      "far",
    ]);
  });

  it("sorts by price with missing quotes last", () => {
    expect(sortCandidates(list, "price").map((c) => c.worker_id)).toEqual([
      "far",
      "pricey",
      "noquote",
    ]);
  });

  it("puts people who quoted first for best match, keeping server order", () => {
    expect(sortCandidates(list, "best").map((c) => c.worker_id)).toEqual([
      "far",
      "pricey",
      "noquote",
    ]);
  });

  it("does not mutate the input", () => {
    const before = list.map((c) => c.worker_id);
    sortCandidates(list, "closest");
    expect(list.map((c) => c.worker_id)).toEqual(before);
  });

  it("prices a candidate from their quote, else the budget", () => {
    expect(candidatePrice(candidate({ quoted_amount: 25 }), { budget_amount: 30 })).toBe(25);
    expect(candidatePrice(candidate({}), { budget_amount: 30 })).toBe(30);
    expect(candidatePrice(candidate({}), { budget_amount: null })).toBeNull();
  });
});

describe("depositFor", () => {
  it("holds 30% so the on-site quote can exceed it", () => {
    expect(depositFor(30)).toBe(9);
    expect(depositFor(2)).toBe(1);
    expect(depositFor(null)).toBe(5);
    expect(depositFor(100)).toBeLessThan(100);
  });
});

describe("tracking steps", () => {
  it.each([
    ["REQUESTED", 0],
    ["BOOKED", 1],
    ["IN_PROGRESS", 3],
    ["DISPUTED", 3],
    ["COMPLETED", 4],
  ] as const)("%s has %i completed steps", (status, steps) => {
    expect(completedSteps(status)).toBe(steps);
  });
});

describe("review and record text", () => {
  it("folds stars, tags and note together", () => {
    expect(composeReview(4, ["On time", "Polite"], " Great ")).toBe(
      "★★★★☆ — On time, Polite — Great",
    );
    expect(composeReview(0, [], "  ")).toBeUndefined();
  });

  it("summarises the job from its first description line", () => {
    expect(summariseJob({ trade: "PLUMBING", problem_description: "Leak\nNeeded: Today" })).toBe(
      "Plumber job: Leak",
    );
    expect(summariseJob({ trade: "SOLAR", problem_description: null })).toBe("Solar installer job");
  });
});

describe("timing in descriptions", () => {
  it("round-trips the timing line", () => {
    const text = withTiming("Gate hinge snapped", "Today");
    expect(text).toBe("Gate hinge snapped\nNeeded: Today");
    expect(splitTiming(text)).toEqual({ text: "Gate hinge snapped", timing: "Today" });
  });

  it("handles descriptions without timing", () => {
    expect(splitTiming("Just a leak")).toEqual({ text: "Just a leak", timing: null });
    expect(splitTiming(null)).toEqual({ text: "", timing: null });
  });
});

describe("matchExplanation", () => {
  it("explains a new worker without inventing a record", () => {
    const text = matchExplanation(
      candidate({
        jobs_completed: 0,
        distance_band: "SAME_SUBURB",
        distance_km: 0,
        suburb: "Entumbane",
      }),
      "PLUMBING",
    );
    expect(text).toBe(
      "Registered for plumber work, same suburb — based in Entumbane, 0.0 km away. New on Maricho, so there's no track record yet.",
    );
  });

  it("summarises an experienced worker's record", () => {
    const text = matchExplanation(
      candidate({ grade: "EXPERT", jobs_completed: 31, on_time_rate: 96, dispute_rate: 2 }),
      "PLUMBING",
    );
    expect(text).toContain("Expert with 31 jobs done: 96% on time, 2% disputed.");
    expect(text).not.toMatch(/Enum|PLUMBING/);
  });
});

describe("inDrive-style responses", () => {
  const base = {
    worker_id: "w",
    suburb: "Hillside",
    travel_means: null,
    distance_band: "SAME_SUBURB" as const,
    distance_km: 1,
    grade: "EXPERT" as const,
    on_time_rate: 95,
    dispute_rate: 0,
    fill_rate: 90,
    jobs_completed: 10,
    reason: "",
    availability_note: null,
    quoted_at: null,
  };

  it("only workers who answered can be approved; the rest are counted", () => {
    const { responded, waiting } = splitResponders(
      [
        { ...base, worker_id: "a", quoted_amount: 40 },
        { ...base, worker_id: "b", quoted_amount: null },
        { ...base, worker_id: "c", quoted_amount: 35 },
      ],
      "price",
    );
    expect(responded.map((candidate) => candidate.worker_id)).toEqual(["c", "a"]);
    expect(waiting).toBe(1);
  });

  it("says whether they accepted the price or offered another", () => {
    expect(responseLabel({ quoted_amount: 40 }, 40)).toBe("Accepted your price");
    expect(responseLabel({ quoted_amount: 35 }, 40)).toBe("Offered $35");
    expect(responseLabel({ quoted_amount: 50 }, null)).toBe("Offered $50");
    expect(responseLabel({ quoted_amount: null }, 40)).toBeNull();
  });
});
