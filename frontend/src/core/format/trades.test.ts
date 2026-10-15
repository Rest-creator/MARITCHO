import { describe, expect, it } from "vitest";

import {
  ALL_SKILLS,
  TRADES,
  describeWithSkill,
  findSkill,
  matchSkills,
  searchSkills,
  tradeIcon,
  tradeLabel,
} from "@/core/format/trades";

describe("skill catalogue", () => {
  it("covers every backend trade with a selectable skill", () => {
    for (const trade of TRADES) {
      expect(ALL_SKILLS.some((skill) => skill.trade === trade)).toBe(true);
    }
  });

  it("has unique skill ids", () => {
    const ids = ALL_SKILLS.map((skill) => skill.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("finds skills by id", () => {
    expect(findSkill("tiler")?.trade).toBe("BUILDING");
    expect(findSkill("gardener")?.trade).toBeNull();
    expect(findSkill("nope")).toBeUndefined();
    expect(findSkill(null)).toBeUndefined();
  });

  it("searches case-insensitively and drops empty groups", () => {
    const groups = searchSkills("WELD");
    expect(groups).toHaveLength(1);
    expect(groups[0]?.skills.map((skill) => skill.label)).toEqual(["Welder"]);
    expect(searchSkills("")).toHaveLength(4);
    expect(searchSkills("zzz")).toEqual([]);
  });
});

describe("describeWithSkill", () => {
  it("prefixes a skill narrower than its trade", () => {
    const tiler = findSkill("tiler");
    expect(tiler).toBeDefined();
    expect(describeWithSkill(tiler!, " Retile the shower ")).toBe("Tiler: Retile the shower");
  });

  it("leaves the text alone when the skill is the trade itself", () => {
    expect(describeWithSkill(findSkill("plumber")!, "Leaking tap")).toBe("Leaking tap");
  });
});

describe("trade labels", () => {
  it("gives every trade a label and icon", () => {
    for (const trade of TRADES) {
      expect(tradeLabel(trade)).not.toBe("");
      expect(tradeIcon(trade)).not.toBe("");
    }
  });
});

describe("matchSkills (free text)", () => {
  const labels = (text: string): string[] => matchSkills(text).map((skill) => skill.label);

  it("finds the skill from everyday words, in a whole sentence", () => {
    expect(labels("I fix geysers and leaking taps")[0]).toBe("Plumber");
    expect(labels("gate welding")[0]).toBe("Welder");
    expect(labels("solar panels and inverters")[0]).toBe("Solar installer");
    expect(labels("fridge repair")[0]).toBe("Appliance repair");
  });

  it("ranks the skill most words point at first", () => {
    expect(labels("wiring sockets and lights")[0]).toBe("Electrician");
  });

  it("matches nothing for empty or unrelated text", () => {
    expect(matchSkills("")).toEqual([]);
    expect(matchSkills("  ")).toEqual([]);
    expect(matchSkills("astronaut")).toEqual([]);
  });
});
