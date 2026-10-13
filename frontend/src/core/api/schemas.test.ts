import { describe, expect, it } from "vitest";

import { matchCandidateSchema, openJobSchema, userSchema } from "@/core/api/schemas";

describe("backend contracts", () => {
  it("coerces Pydantic Decimal strings to numbers", () => {
    const parsed = openJobSchema.parse({
      job_id: "6b0b",
      trade: "WELDING",
      suburb: "Avondale",
      budget_amount: "45.00",
      problem_description: "Gate hinge",
      created_at: "2026-10-13T10:00:00Z",
      distance_band: "NEARBY",
      distance_km: 3.2,
    });
    expect(parsed.budget_amount).toBe(45);
  });

  it("keeps nullable decimals null", () => {
    const parsed = matchCandidateSchema.parse({
      worker_id: "w",
      suburb: "Mbare",
      travel_means: null,
      distance_band: "FAR",
      distance_km: 12,
      grade: "APPRENTICE",
      on_time_rate: "80.00",
      dispute_rate: "0.00",
      fill_rate: "100.00",
      jobs_completed: 4,
      reason: "Skilled",
      quoted_amount: null,
      availability_note: null,
      quoted_at: null,
    });
    expect(parsed.quoted_amount).toBeNull();
    expect(parsed.on_time_rate).toBe(80);
  });

  it("rejects values outside the backend enums", () => {
    expect(() => userSchema.parse({ id: "1", phone: "+263", role: "ADMIN" })).toThrow();
  });

  it("rejects non-numeric decimals", () => {
    expect(() =>
      openJobSchema.parse({
        job_id: "x",
        trade: "SOLAR",
        suburb: "s",
        budget_amount: "abc",
        problem_description: null,
        created_at: null,
        distance_band: "NEARBY",
        distance_km: 1,
      }),
    ).toThrow();
  });
});
