import type { Trade } from "@/core/api/schemas";
import type { IconName } from "@/components/ui/Icon";

/*
 * The design's skill catalogue is broader than the backend's TradeEnum
 * (six trades in Stage One). Skills that map to a backend trade are
 * selectable; the rest are shown as "soon" so people can see where
 * Maricho is heading without being able to post a job nobody can match.
 */

export interface SkillOption {
  id: string;
  label: string;
  trade: Trade | null;
}

export interface SkillGroup {
  title: string;
  skills: readonly SkillOption[];
}

export const SKILL_GROUPS: readonly SkillGroup[] = [
  {
    title: "Home & building",
    skills: [
      { id: "plumber", label: "Plumber", trade: "PLUMBING" },
      { id: "electrician", label: "Electrician", trade: "ELECTRICAL" },
      { id: "bricklayer", label: "Bricklayer", trade: "BUILDING" },
      { id: "tiler", label: "Tiler", trade: "BUILDING" },
      { id: "roof-leak", label: "Roof leak repair", trade: "BUILDING" },
      { id: "painter", label: "Painter", trade: "BUILDING" },
      { id: "welder", label: "Welder", trade: "WELDING" },
      { id: "solar", label: "Solar installer", trade: "SOLAR" },
      { id: "appliance", label: "Appliance repair", trade: "APPLIANCE_REPAIR" },
    ],
  },
  {
    title: "Outdoor & farm",
    skills: [
      { id: "gardener", label: "Gardener", trade: null },
      { id: "grass-cutter", label: "Grass cutter", trade: null },
      { id: "tree-cutter", label: "Tree cutter", trade: null },
      { id: "farm-worker", label: "Farm worker", trade: null },
      { id: "trencher", label: "Trencher", trade: null },
    ],
  },
  {
    title: "Care & household",
    skills: [
      { id: "house-help", label: "House help", trade: null },
      { id: "baby-sitter", label: "Baby sitter", trade: null },
      { id: "laundry", label: "Laundry", trade: null },
      { id: "dog-walker", label: "Dog walker", trade: null },
      { id: "school-run", label: "School run driver", trade: null },
    ],
  },
  {
    title: "Vehicles",
    skills: [
      { id: "mechanic", label: "Motor mechanic", trade: null },
      { id: "panel-beater", label: "Panel beater", trade: null },
      { id: "car-washer", label: "Car washer", trade: null },
    ],
  },
];

export const ALL_SKILLS: readonly SkillOption[] = SKILL_GROUPS.flatMap((group) => group.skills);

export function findSkill(id: string | null | undefined): SkillOption | undefined {
  return ALL_SKILLS.find((skill) => skill.id === id);
}

export function searchSkills(query: string): SkillGroup[] {
  const needle = query.trim().toLowerCase();
  if (needle === "") return [...SKILL_GROUPS];
  return SKILL_GROUPS.map((group) => ({
    ...group,
    skills: group.skills.filter((skill) => skill.label.toLowerCase().includes(needle)),
  })).filter((group) => group.skills.length > 0);
}

const TRADE_LABELS: Record<Trade, string> = {
  PLUMBING: "Plumber",
  ELECTRICAL: "Electrician",
  SOLAR: "Solar installer",
  WELDING: "Welder",
  BUILDING: "Builder",
  APPLIANCE_REPAIR: "Appliance repair",
};

export function tradeLabel(trade: Trade): string {
  return TRADE_LABELS[trade];
}

const TRADE_WORK_LABELS: Record<Trade, string> = {
  PLUMBING: "Plumbing",
  ELECTRICAL: "Electrical",
  SOLAR: "Solar",
  WELDING: "Welding",
  BUILDING: "Building",
  APPLIANCE_REPAIR: "Appliances",
};

/** "Welding" rather than "Welder" — for filters that describe the work. */
export function tradeWorkLabel(trade: Trade): string {
  return TRADE_WORK_LABELS[trade];
}

const TRADE_ICONS: Record<Trade, IconName> = {
  PLUMBING: "drop",
  ELECTRICAL: "bolt",
  SOLAR: "sun",
  WELDING: "flame",
  BUILDING: "bricks",
  APPLIANCE_REPAIR: "appliance",
};

export function tradeIcon(trade: Trade): IconName {
  return TRADE_ICONS[trade];
}

export const TRADES: readonly Trade[] = [
  "PLUMBING",
  "ELECTRICAL",
  "SOLAR",
  "WELDING",
  "BUILDING",
  "APPLIANCE_REPAIR",
];

/**
 * Prefix the specific skill when it is narrower than the backend trade
 * ("Tiler" → BUILDING), so the worker still sees exactly what's needed.
 */
export function describeWithSkill(skill: SkillOption, description: string): string {
  const text = description.trim();
  if (skill.trade === null || TRADE_LABELS[skill.trade] === skill.label) {
    return text;
  }
  return `${skill.label}: ${text}`;
}
