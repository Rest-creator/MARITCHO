import { describe, expect, it } from "vitest";

import { safeNextPath, withNext } from "@/core/session/next-path";

describe("safeNextPath", () => {
  it("accepts same-site paths", () => {
    expect(safeNextPath("/worker/jobs/abc")).toBe("/worker/jobs/abc");
    expect(safeNextPath(["/worker", "/employer"])).toBe("/worker");
  });

  it.each([
    undefined,
    null,
    "",
    "worker",
    "https://evil.example",
    "//evil.example",
    "/\\evil.example",
    "/\t/evil.example",
    `/${"a".repeat(600)}`,
  ])("rejects %s", (value) => {
    expect(safeNextPath(value)).toBeNull();
  });
});

describe("withNext", () => {
  it("appends next with the right separator", () => {
    expect(withNext("/worker/skills", null)).toBe("/worker/skills");
    expect(withNext("/worker/skills", "/worker/jobs/1")).toBe(
      "/worker/skills?next=%2Fworker%2Fjobs%2F1",
    );
    expect(withNext("/signup?role=worker", "/worker/jobs/1")).toBe(
      "/signup?role=worker&next=%2Fworker%2Fjobs%2F1",
    );
  });
});
