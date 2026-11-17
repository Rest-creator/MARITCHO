import { describe, expect, it } from "vitest";

import { canActAs, hasBothSides } from "@/core/session/roles";

describe("account sides", () => {
  it("uses the active role, plus any other side the account has unlocked", () => {
    const dual = { role: "BUYER" as const, roles: ["BUYER" as const, "WORKER" as const] };
    expect(canActAs(dual, "BUYER")).toBe(true);
    expect(canActAs(dual, "WORKER")).toBe(true);
    expect(hasBothSides(dual)).toBe(true);
  });

  it("keeps single-sided and older sessions (no roles field) to their side", () => {
    expect(canActAs({ role: "WORKER", roles: ["WORKER"] }, "BUYER")).toBe(false);
    expect(canActAs({ role: "WORKER" }, "WORKER")).toBe(true);
    expect(hasBothSides({ role: "WORKER" })).toBe(false);
    expect(canActAs(null, "BUYER")).toBe(false);
  });
});
