import { describe, expect, it } from "vitest";

import {
  distanceBandLabel,
  firstName,
  formatDayLabel,
  formatKm,
  formatLocalPhone,
  formatMoney,
  formatPercent,
  formatRelativeTime,
  greeting,
  initials,
  isVerifiedGrade,
  jobStatusLabel,
  toInternationalPhone,
} from "@/core/format/format";

const NOW = new Date("2026-10-13T12:00:00Z");

describe("formatMoney", () => {
  it("drops cents for whole amounts and keeps them otherwise", () => {
    expect(formatMoney(30)).toBe("$30");
    expect(formatMoney(30.5)).toBe("$30.50");
    expect(formatMoney(1200)).toBe("$1,200");
  });

  it("prefixes ZWG and shows a dash for missing amounts", () => {
    expect(formatMoney(15, "ZWG")).toBe("ZWG 15");
    expect(formatMoney(null)).toBe("—");
  });
});

describe("formatRelativeTime", () => {
  it.each([
    ["2026-10-13T11:59:30Z", "just now"],
    ["2026-10-13T11:52:00Z", "8 min ago"],
    ["2026-10-13T11:00:00Z", "1 hour ago"],
    ["2026-10-13T10:00:00Z", "2 hours ago"],
    ["2026-10-12T12:00:00Z", "1 day ago"],
    ["2026-10-10T12:00:00Z", "3 days ago"],
  ])("%s → %s", (iso, expected) => {
    expect(formatRelativeTime(iso, NOW)).toBe(expected);
  });

  it("falls back to a short date after a week and handles empty input", () => {
    expect(formatRelativeTime("2026-09-12T12:00:00Z", NOW)).toBe("12 Sept");
    expect(formatRelativeTime(null, NOW)).toBe("");
  });
});

describe("formatDayLabel", () => {
  it("labels today and yesterday", () => {
    expect(formatDayLabel("2026-10-13T08:00:00Z", NOW)).toBe("Today");
    expect(formatDayLabel("2026-10-12T08:00:00Z", NOW)).toBe("Yesterday");
  });
});

describe("greeting", () => {
  it("follows the time of day", () => {
    expect(greeting(new Date(2026, 9, 13, 8))).toBe("Good morning");
    expect(greeting(new Date(2026, 9, 13, 14))).toBe("Good afternoon");
    expect(greeting(new Date(2026, 9, 13, 19))).toBe("Good evening");
  });
});

describe("names", () => {
  it("builds initials from first and last name", () => {
    expect(initials("Rudo Kanengoni")).toBe("RK");
    expect(initials("tafadzwa")).toBe("T");
    expect(initials("  ")).toBe("?");
    expect(initials("Kudzai Tendai Ncube")).toBe("KN");
  });

  it("extracts the first name", () => {
    expect(firstName("Rudo Kanengoni")).toBe("Rudo");
    expect(firstName("")).toBe("");
  });
});

describe("phone numbers", () => {
  it("normalises local Zimbabwean numbers to +263", () => {
    expect(toInternationalPhone("77 412 3089")).toBe("+263774123089");
    expect(toInternationalPhone("0774123089")).toBe("+263774123089");
    expect(toInternationalPhone("+263 77 412 3089")).toBe("+263774123089");
  });

  it("formats an international number for display", () => {
    expect(formatLocalPhone("+263774123089")).toBe("77 412 3089");
  });
});

describe("labels", () => {
  it("formats distances and rates", () => {
    expect(formatKm(3.24)).toBe("3.2 km");
    expect(formatKm(12.6)).toBe("13 km");
    expect(formatPercent(0.925)).toBe("93%");
  });

  it("maps enums to plain words", () => {
    expect(distanceBandLabel("SAME_SUBURB")).toBe("Same suburb");
    expect(jobStatusLabel("MATCHED")).toBe("Offers in");
    expect(isVerifiedGrade("REGISTERED")).toBe(false);
    expect(isVerifiedGrade("EXPERT")).toBe(true);
  });
});
