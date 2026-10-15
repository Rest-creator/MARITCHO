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
  /** Everyday words people use for this work ("geyser", "gate"), for free-text search. */
  keywords?: readonly string[];
}

export interface SkillGroup {
  title: string;
  skills: readonly SkillOption[];
}

export const SKILL_GROUPS: readonly SkillGroup[] = [
  {
    title: "Home & building",
    skills: [
      {
        id: "plumber",
        label: "Plumber",
        trade: "PLUMBING",
        keywords: [
          "plumbing",
          "pipe",
          "tap",
          "leak",
          "geyser",
          "toilet",
          "drain",
          "sink",
          "borehole",
          "tank",
          "water",
        ],
      },
      {
        id: "electrician",
        label: "Electrician",
        trade: "ELECTRICAL",
        keywords: [
          "electrical",
          "wiring",
          "wire",
          "socket",
          "plug",
          "light",
          "switch",
          "power",
          "breaker",
          "electric",
        ],
      },
      {
        id: "bricklayer",
        label: "Bricklayer",
        trade: "BUILDING",
        keywords: ["brick", "wall", "build", "builder", "construction", "plaster", "foundation"],
      },
      { id: "tiler", label: "Tiler", trade: "BUILDING", keywords: ["tile", "tiling", "floor"] },
      {
        id: "roof-leak",
        label: "Roof leak repair",
        trade: "BUILDING",
        keywords: ["roof", "roofing", "gutter", "ceiling"],
      },
      { id: "painter", label: "Painter", trade: "BUILDING", keywords: ["paint", "painting"] },
      {
        id: "welder",
        label: "Welder",
        trade: "WELDING",
        keywords: ["welding", "weld", "gate", "burglar", "bars", "metal", "steel", "fabrication"],
      },
      {
        id: "solar",
        label: "Solar installer",
        trade: "SOLAR",
        keywords: ["solar", "panel", "inverter", "battery"],
      },
      {
        id: "appliance",
        label: "Appliance repair",
        trade: "APPLIANCE_REPAIR",
        keywords: [
          "fridge",
          "freezer",
          "stove",
          "washing",
          "microwave",
          "appliance",
          "repair",
          "kettle",
        ],
      },
    ],
  },
  {
    title: "Outdoor & farm",
    skills: [
      {
        id: "gardener",
        label: "Gardener",
        trade: null,
        keywords: ["garden", "gardening", "hedge", "flowers"],
      },
      {
        id: "grass-cutter",
        label: "Grass cutter",
        trade: null,
        keywords: ["grass", "lawn", "mowing", "slashing"],
      },
      {
        id: "tree-cutter",
        label: "Tree cutter",
        trade: null,
        keywords: ["tree", "trees", "branches"],
      },
      {
        id: "farm-worker",
        label: "Farm worker",
        trade: null,
        keywords: ["farm", "farming", "crops", "planting", "harvest"],
      },
      { id: "trencher", label: "Trencher", trade: null, keywords: ["trench", "digging", "dig"] },
    ],
  },
  {
    title: "Care & household",
    skills: [
      {
        id: "house-help",
        label: "House help",
        trade: null,
        keywords: ["cleaning", "clean", "housework", "maid"],
      },
      {
        id: "baby-sitter",
        label: "Baby sitter",
        trade: null,
        keywords: ["baby", "babysitting", "child", "children", "nanny"],
      },
      { id: "laundry", label: "Laundry", trade: null, keywords: ["washing", "ironing", "clothes"] },
      { id: "dog-walker", label: "Dog walker", trade: null, keywords: ["dog", "dogs", "pets"] },
      {
        id: "school-run",
        label: "School run driver",
        trade: null,
        keywords: ["driver", "driving", "school", "transport"],
      },
    ],
  },
  {
    title: "Vehicles",
    skills: [
      {
        id: "mechanic",
        label: "Motor mechanic",
        trade: null,
        keywords: ["car", "engine", "vehicle", "service", "motor"],
      },
      {
        id: "panel-beater",
        label: "Panel beater",
        trade: null,
        keywords: ["panel", "dent", "spray", "body"],
      },
      { id: "car-washer", label: "Car washer", trade: null, keywords: ["car", "wash", "valet"] },
    ],
  },
];

export const ALL_SKILLS: readonly SkillOption[] = SKILL_GROUPS.flatMap((group) => group.skills);

export function findSkill(id: string | null | undefined): SkillOption | undefined {
  return ALL_SKILLS.find((skill) => skill.id === id);
}

const STOP_WORDS = new Set([
  "and",
  "the",
  "can",
  "fix",
  "for",
  "with",
  "work",
  "jobs",
  "job",
  "do",
  "i",
]);

/** The words in what someone typed that are worth matching ("I fix geysers" → ["geysers"]). */
function searchWords(text: string): string[] {
  return text
    .toLowerCase()
    .split(/[^a-z]+/)
    .filter((word) => word.length >= 3 && !STOP_WORDS.has(word));
}

function skillTerms(skill: SkillOption): string[] {
  return [...skill.label.toLowerCase().split(/\s+/), ...(skill.keywords ?? [])];
}

/** "welding" matches "weld", "geysers" matches "geyser": either may be the other's start. */
function wordMatches(word: string, term: string): boolean {
  return term.startsWith(word) || (term.length >= 4 && word.startsWith(term));
}

/** How many of the typed words point at this skill (0 = not a match). */
function skillScore(skill: SkillOption, words: readonly string[]): number {
  const terms = skillTerms(skill);
  return words.filter((word) => terms.some((term) => wordMatches(word, term))).length;
}

/**
 * Skills matching free text, best first: a single word ("weld") or a
 * whole sentence ("I fix geysers and leaking taps"). Empty text matches
 * nothing — the list stays hidden until someone asks for it.
 */
export function matchSkills(text: string): SkillOption[] {
  const words = searchWords(text);
  if (words.length === 0) return [];
  return ALL_SKILLS.map((skill) => ({ skill, score: skillScore(skill, words) }))
    .filter((entry) => entry.score > 0)
    .sort((a, b) => b.score - a.score)
    .map((entry) => entry.skill);
}

export function searchSkills(query: string): SkillGroup[] {
  if (query.trim() === "") return [...SKILL_GROUPS];
  const matches = new Set(matchSkills(query).map((skill) => skill.id));
  return SKILL_GROUPS.map((group) => ({
    ...group,
    skills: group.skills.filter((skill) => matches.has(skill.id)),
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
