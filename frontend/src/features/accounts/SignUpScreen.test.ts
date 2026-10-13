import { describe, expect, it } from "vitest";

import { validateSignUp } from "@/features/accounts/SignUpScreen";
import { validatePostJob } from "@/features/jobs/PostJobScreen";
import { findSkill } from "@/core/format/trades";

describe("validateSignUp", () => {
  it("requires a name for new accounts but not for log in", () => {
    expect(validateSignUp("", "77 412 3089", false)).toMatch(/name/);
    expect(validateSignUp("", "77 412 3089", true)).toBeNull();
  });

  it("accepts 9-digit local numbers with or without a leading 0", () => {
    expect(validateSignUp("Rudo", "77 412 3089", false)).toBeNull();
    expect(validateSignUp("Rudo", "0774123089", false)).toBeNull();
    expect(validateSignUp("Rudo", "7741", false)).toMatch(/mobile number/);
  });
});

describe("validatePostJob", () => {
  const location = { suburb: "Borrowdale", address: "14 Harrow Rd", landmark: "" };

  it("asks for a skill, a description and a place, in that order", () => {
    expect(validatePostJob(null, "Leaking tap", location)).toMatch(/who you need/);
    expect(validatePostJob(findSkill("gardener")!, "Cut the lawn", location)).toMatch(
      /who you need/,
    );
    expect(validatePostJob(findSkill("plumber")!, "leak", location)).toMatch(/few words/);
    expect(
      validatePostJob(findSkill("plumber")!, "Leaking tap", { ...location, address: " " }),
    ).toMatch(/where/);
    expect(validatePostJob(findSkill("plumber")!, "Leaking tap", location)).toBeNull();
  });
});
