import { describe, expect, it } from "vitest";

import { MAX_TRAVEL_KM, MIN_TRAVEL_KM, clampTravelKm } from "@/core/format/travel";

describe("travel distance", () => {
  it("allows the full 1–50 km the backend accepts (not the old 25 km cap)", () => {
    expect(MIN_TRAVEL_KM).toBe(1);
    expect(MAX_TRAVEL_KM).toBe(50);
    expect(clampTravelKm(40)).toBe(40);
  });

  it("keeps out-of-range or broken values inside the limits", () => {
    expect(clampTravelKm(0)).toBe(1);
    expect(clampTravelKm(80)).toBe(50);
    expect(clampTravelKm(12.6)).toBe(13);
    expect(clampTravelKm(Number.NaN)).toBe(1);
  });
});
