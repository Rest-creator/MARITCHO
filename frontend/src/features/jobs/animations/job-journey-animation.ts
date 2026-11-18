import {
  animated,
  composition,
  ellipse,
  fill,
  group,
  hex,
  polyline,
  shapeLayer,
  still,
  stroke,
  transform,
  trim,
  type LottieAnimation,
  type Marker,
  type ShapeItem,
  type ShapeLayer,
} from "@/core/motion/lottie-builders";
import {
  JOURNEY_ARRIVE,
  JOURNEY_BLOCK,
  JOURNEY_FRAMES,
  JOURNEY_STEPS,
} from "@/features/jobs/animations/job-journey-timeline";

/*
 * Geometry mirrors the CSS `.stepper` grid: 4 equal columns, 4px gaps, 4px
 * bars with round caps — so the animated bars sit exactly above the labels.
 */
const WIDTH = 320;
const HEIGHT = 12;
const GAP = 4;
const BAR_Y = HEIGHT / 2;
const BAR_WIDTH = (WIDTH - GAP * (JOURNEY_STEPS - 1)) / JOURNEY_STEPS;
const STROKE = 4;
const CAP = STROKE / 2;

const TRACK = hex("#ffffff");
const DONE = hex("#00ace8"); // --emerald
const CURRENT = hex("#00abe3"); // --amber
const GLINT = hex("#e0f7ff"); // --amber-pale
const RUNNER = hex("#67d6fa"); // --amber-lighter

function barStart(step: number): number {
  return step * (BAR_WIDTH + GAP) + CAP;
}

function barEnd(step: number): number {
  return step * (BAR_WIDTH + GAP) + BAR_WIDTH - CAP;
}

function bar(step: number): ShapeItem {
  return polyline([
    [barStart(step), BAR_Y],
    [barEnd(step), BAR_Y],
  ]);
}

function arriveStart(level: number): number {
  return level * JOURNEY_BLOCK;
}

function arriveEnd(level: number): number {
  return level * JOURNEY_BLOCK + JOURNEY_ARRIVE;
}

function idleEnd(level: number): number {
  return (level + 1) * JOURNEY_BLOCK;
}

const steps: number[] = Array.from({ length: JOURNEY_STEPS }, (_, step) => step);
const levels: number[] = Array.from({ length: JOURNEY_STEPS + 1 }, (_, level) => level);

/**
 * A bright dash that runs along `step`'s bar starting at `from`. It is hidden
 * outside its run: with round caps a fully trimmed (zero-length) path still
 * paints a dot, which would otherwise sit at the bar's end at rest.
 */
function glint(step: number, from: number): ShapeItem {
  return group(
    `glint-${step}`,
    [
      bar(step),
      stroke(GLINT, STROKE, 75),
      trim(
        animated([
          [from + 5, 0],
          [from + 19, 100],
        ]),
        animated([
          [from, 0],
          [from + 14, 100],
        ]),
      ),
    ],
    transform({
      opacity: animated([
        [from, 0],
        [from + 1, 100],
        [from + 17, 100],
        [from + 18, 0],
      ]),
    }),
  );
}

function trackLayer(): ShapeLayer {
  return shapeLayer({
    index: 0,
    name: "track",
    inPoint: 0,
    outPoint: JOURNEY_FRAMES,
    shapes: steps.map((step) => group(`track-${step}`, [bar(step), stroke(TRACK, STROKE, 10)])),
  });
}

/** Bar `step` fills during the arrival into level `step + 1`, then holds. */
function fillLayer(): ShapeLayer {
  return shapeLayer({
    index: 0,
    name: "done",
    inPoint: 0,
    outPoint: JOURNEY_FRAMES,
    shapes: steps.map((step) =>
      group(`done-${step}`, [
        bar(step),
        stroke(DONE, STROKE),
        trim(
          still(0),
          animated([
            [arriveStart(step + 1), 0],
            [arriveEnd(step + 1), 100],
          ]),
        ),
      ]),
    ),
  });
}

/** The current step: tinted, with a glint sweeping across it while idle. */
function currentLayer(level: number): ShapeLayer {
  return shapeLayer({
    index: 0,
    name: `current-${level}`,
    inPoint: arriveEnd(level),
    // Stays under the fill during the next arrival so the tint is "filled in".
    outPoint: Math.min(JOURNEY_FRAMES, idleEnd(level) + JOURNEY_ARRIVE),
    shapes: [
      glint(level, arriveEnd(level)),
      group(`tint-${level}`, [bar(level), stroke(CURRENT, STROKE, 40)]),
    ],
  });
}

/**
 * Level 4 (job signed off): one sweep across all four bars, each a frame
 * behind the last so it reads as a single wave. A glint lasts 19 frames, so
 * the last one ends exactly on the final frame.
 */
function finishLayer(): ShapeLayer {
  const from: number = arriveEnd(JOURNEY_STEPS);
  return shapeLayer({
    index: 0,
    name: "finish",
    inPoint: from,
    outPoint: JOURNEY_FRAMES,
    shapes: steps.map((step) => glint(step, from + step)),
  });
}

/** A soft dot riding the front of the fill during every arrival. */
function runnerLayer(): ShapeLayer {
  const arrivals: number[] = levels.filter((level) => level > 0);
  return shapeLayer({
    index: 0,
    name: "runner",
    inPoint: 0,
    outPoint: JOURNEY_FRAMES,
    position: animated(
      arrivals.flatMap((level): [number, number[]][] => [
        [arriveStart(level), [barStart(level - 1), BAR_Y, 0]],
        [arriveEnd(level), [barEnd(level - 1), BAR_Y, 0]],
      ]),
    ),
    opacity: animated([
      [0, 0],
      ...arrivals.flatMap((level): [number, number][] => [
        [arriveStart(level), 0],
        [arriveStart(level) + 2, 90],
        [arriveEnd(level) - 3, 90],
        [arriveEnd(level), 0],
      ]),
    ]),
    shapes: [group("runner", [ellipse(10), fill(RUNNER)], transform())],
  });
}

function markers(): Marker[] {
  return levels.flatMap((level): Marker[] => [
    { tm: arriveStart(level), dr: JOURNEY_ARRIVE, cm: `level-${level}-arrive` },
    { tm: arriveEnd(level), dr: JOURNEY_BLOCK - JOURNEY_ARRIVE, cm: `level-${level}-idle` },
  ]);
}

export function buildJobJourneyAnimation(): LottieAnimation {
  return composition({
    name: "maritcho-job-journey",
    width: WIDTH,
    height: HEIGHT,
    frames: JOURNEY_FRAMES,
    // Top-most first.
    layers: [
      runnerLayer(),
      finishLayer(),
      fillLayer(),
      ...steps.map((step) => currentLayer(step)),
      trackLayer(),
    ],
    markers: markers(),
  });
}
