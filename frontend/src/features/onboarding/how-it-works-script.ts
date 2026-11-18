import {
  buildTheatreState,
  valueAt,
  type KeyframeTrack,
  type TheatreProjectState,
} from "@/core/motion/theatre-state";

/**
 * "How Maritcho works" — one choreography, used two ways:
 *  - as Theatre.js keyframes (tweened, scrubbable, editable in Theatre Studio)
 *  - sampled at each chapter's rest time for the static, no-download fallback.
 *
 * Coordinates are in the stage's 320×168 SVG viewBox; each object is drawn
 * around its own centre. Times are seconds on the sheet's sequence.
 */

export const HOW_IT_WORKS_PROJECT = "Maritcho onboarding";
export const HOW_IT_WORKS_SHEET = "How it works";

/** Where the sequence rests at the end of each chapter. */
export const CHAPTER_RESTS: readonly number[] = [1.0, 2.2, 3.4, 4.6];
export const SEQUENCE_LENGTH = 4.6;

export const CHAPTERS: readonly { title: string; caption: string }[] = [
  { title: "Post the job", caption: "Say what's wrong. A photo or a voice note is enough." },
  {
    title: "Get prices",
    caption: "Workers nearby send their price. You choose who to hire.",
  },
  {
    title: "The work gets done",
    caption: "Your worker comes to you. Follow the job as it happens.",
  },
  {
    title: "Sign off",
    caption: "Confirm and pay. Every job builds the worker's record.",
  },
];

export const SCENE_OBJECTS = [
  "jobCard",
  "pin",
  "workerA",
  "workerB",
  "workerC",
  "quote",
  "progress",
  "badge",
  "stars",
] as const;

export type SceneObjectKey = (typeof SCENE_OBJECTS)[number];

export interface SceneValues {
  x: number;
  y: number;
  scale: number;
  opacity: number;
  /** Progress bar fill, 0..1 (only the progress object uses it). */
  fill: number;
}

type SceneProp = keyof SceneValues;

interface ObjectScript {
  /** Value of any prop without a track. Also Theatre's prop default. */
  base: SceneValues;
  tracks: Partial<Record<SceneProp, KeyframeTrack>>;
}

function base(x: number, y: number): SceneValues {
  return { x, y, scale: 1, opacity: 1, fill: 0 };
}

export const SCENE_SCRIPT: Readonly<Record<SceneObjectKey, ObjectScript>> = {
  // 1 · The posted job slides up, then tucks into the corner while prices arrive.
  jobCard: {
    base: base(160, 64),
    tracks: {
      x: [
        [1.1, 160],
        [1.7, 92],
      ],
      y: [
        [0, 88],
        [0.9, 64],
        [1.1, 64],
        [1.7, 40],
      ],
      scale: [
        [0, 0.92],
        [0.9, 1],
        [1.1, 1],
        [1.7, 0.72],
      ],
      opacity: [
        [0, 0],
        [0.6, 1],
        [3.5, 1],
        [3.9, 0],
      ],
    },
  },
  // 2 · The job's pin drops; three workers pop up nearby; one sends a price.
  pin: {
    base: base(104, 118),
    tracks: {
      y: [
        [1.0, 100],
        [1.4, 118],
      ],
      scale: [
        [1.0, 0.4],
        [1.4, 1],
      ],
      opacity: [
        [1.0, 0],
        [1.3, 1],
        [3.6, 1],
        [3.9, 0],
      ],
    },
  },
  workerA: {
    base: base(196, 92),
    tracks: {
      scale: [
        [1.2, 0],
        [1.5, 1],
        [2.2, 1],
        [2.5, 0.6],
      ],
      opacity: [
        [1.2, 0],
        [1.4, 1],
        [2.2, 1],
        [2.5, 0],
      ],
    },
  },
  // 3 · The hired worker travels to the pin while the job progresses.
  workerB: {
    base: base(252, 122),
    tracks: {
      x: [
        [2.4, 252],
        [3.0, 140],
      ],
      y: [
        [2.4, 122],
        [3.0, 112],
      ],
      scale: [
        [1.35, 0],
        [1.65, 1],
      ],
      opacity: [
        [1.35, 0],
        [1.55, 1],
        [3.6, 1],
        [3.9, 0],
      ],
    },
  },
  workerC: {
    base: base(200, 146),
    tracks: {
      scale: [
        [1.5, 0],
        [1.8, 1],
        [2.2, 1],
        [2.5, 0.6],
      ],
      opacity: [
        [1.5, 0],
        [1.7, 1],
        [2.2, 1],
        [2.5, 0],
      ],
    },
  },
  quote: {
    base: base(262, 90),
    tracks: {
      scale: [
        [1.8, 0],
        [2.1, 1],
      ],
      opacity: [
        [1.8, 0],
        [1.95, 1],
        [2.3, 1],
        [2.5, 0],
      ],
    },
  },
  progress: {
    base: base(160, 146),
    tracks: {
      y: [
        [2.4, 154],
        [2.7, 146],
      ],
      opacity: [
        [2.4, 0],
        [2.7, 1],
      ],
      fill: [
        [2.7, 0],
        [3.4, 0.75],
        [3.7, 1],
      ],
    },
  },
  // 4 · Signed off: the badge pops and the stars rise in.
  badge: {
    base: base(160, 70),
    tracks: {
      scale: [
        [3.7, 0],
        [4.1, 1.12],
        [4.3, 1],
      ],
      opacity: [
        [3.7, 0],
        [3.85, 1],
      ],
    },
  },
  stars: {
    base: base(160, 120),
    tracks: {
      y: [
        [4.0, 128],
        [4.4, 120],
      ],
      opacity: [
        [4.0, 0],
        [4.3, 1],
      ],
    },
  },
};

/** Builds a record over every scene object without casts. */
export function mapScene<T>(build: (key: SceneObjectKey) => T): Record<SceneObjectKey, T> {
  return {
    jobCard: build("jobCard"),
    pin: build("pin"),
    workerA: build("workerA"),
    workerB: build("workerB"),
    workerC: build("workerC"),
    quote: build("quote"),
    progress: build("progress"),
    badge: build("badge"),
    stars: build("stars"),
  };
}

/** Scene values at `seconds`, without Theatre (static fallback). */
export function sceneValuesAt(key: SceneObjectKey, seconds: number): SceneValues {
  const { base: start, tracks } = SCENE_SCRIPT[key];
  return {
    x: valueAt(tracks.x, seconds, start.x),
    y: valueAt(tracks.y, seconds, start.y),
    scale: valueAt(tracks.scale, seconds, start.scale),
    opacity: valueAt(tracks.opacity, seconds, start.opacity),
    fill: valueAt(tracks.fill, seconds, start.fill),
  };
}

export function buildHowItWorksState(): TheatreProjectState {
  return buildTheatreState({
    sheetId: HOW_IT_WORKS_SHEET,
    length: SEQUENCE_LENGTH,
    objects: mapScene((key) => SCENE_SCRIPT[key].tracks),
  });
}

/** Fractional chapter for a sequence position (0 = first rest, 3 = last). */
export function chapterProgress(position: number): number {
  const firstRest = CHAPTER_RESTS[0] ?? 0;
  if (position <= firstRest) return 0;
  for (let index = 1; index < CHAPTER_RESTS.length; index += 1) {
    const rest = CHAPTER_RESTS[index] ?? SEQUENCE_LENGTH;
    const previous = CHAPTER_RESTS[index - 1] ?? 0;
    if (position <= rest) {
      return index - 1 + (position - previous) / (rest - previous);
    }
  }
  return CHAPTER_RESTS.length - 1;
}

export function clampChapter(chapter: number): number {
  return Math.max(0, Math.min(CHAPTERS.length - 1, chapter));
}

export function restFor(chapter: number): number {
  return CHAPTER_RESTS[clampChapter(chapter)] ?? 0;
}
