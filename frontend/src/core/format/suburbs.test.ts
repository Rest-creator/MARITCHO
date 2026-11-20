import { describe, expect, it } from "vitest";

import {
  DEFAULT_SUBURBS,
  findNearestSuburb,
  matchSuburbs,
  mergeSuburbs,
  predictSuburb,
  resolveSuburbForJob,
} from "@/core/format/suburbs";

describe("suburb matching & autofill prediction", () => {
  it("returns all suburbs when query is empty", () => {
    expect(matchSuburbs("")).toEqual(DEFAULT_SUBURBS);
    expect(predictSuburb("")).toBeNull();
  });

  it("narrows close matches as the user types until the right match", () => {
    expect(matchSuburbs("N")).toEqual(["Njube", "Nkulumane"]);
    expect(matchSuburbs("Nk")).toEqual(["Nkulumane"]);
    expect(predictSuburb("Hil")).toBe("Hillside");
    expect(predictSuburb("ent")).toBe("Entumbane");
  });

  it("handles fuzzy close matches and common local spelling variations", () => {
    expect(predictSuburb("Khumalo")).toBe("Kumalo");
    expect(predictSuburb("Hilside")).toBe("Hillside");
  });

  it("merges server suburbs with default suburbs without duplicates", () => {
    const merged = mergeSuburbs([
      { name: "Borrowdale", latitude: -17.75, longitude: 31.08 },
      { name: "hillside", latitude: -20.185, longitude: 28.63 },
    ]);
    expect(merged).toContain("Borrowdale");
    expect(merged.filter((item) => item.toLowerCase() === "hillside")).toHaveLength(1);
  });

  it("resolves known and custom write-in suburbs for job requests", () => {
    expect(resolveSuburbForJob("hillside", "14 Harrow Rd")).toEqual({
      suburb: "Hillside",
      address: "14 Harrow Rd",
    });

    const custom = resolveSuburbForJob("Burnside", "14 Harrow Rd");
    expect(DEFAULT_SUBURBS).toContain(custom.suburb);
    expect(custom.address).toBe("14 Harrow Rd, Burnside");
  });

  it("finds the nearest suburb from GPS coordinates", () => {
    const nearHillside = findNearestSuburb(-20.184, 28.629);
    expect(nearHillside.suburb).toBe("Hillside");
    expect(nearHillside.distanceKm).toBeLessThan(1);

    const nearNkulumane = findNearestSuburb(-20.206, 28.531);
    expect(nearNkulumane.suburb).toBe("Nkulumane");
  });
});
