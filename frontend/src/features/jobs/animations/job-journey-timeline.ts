import type { AnimationItem } from "lottie-web";

/**
 * Frame layout of the job-journey animation — the contract an After Effects
 * replacement must keep (one marker per block, 30 fps):
 *
 *   level L (0..4) = number of tracking steps done (see `completedSteps`)
 *   [L*BLOCK, L*BLOCK + ARRIVE)        "level-L-arrive": bar L-1 fills
 *   [L*BLOCK + ARRIVE, (L+1)*BLOCK)    "level-L-idle":  current bar shimmers
 *                                      (level 4: one finishing sweep)
 */
export const JOURNEY_STEPS = 4;
export const JOURNEY_BLOCK = 36;
export const JOURNEY_ARRIVE = 14;
export const JOURNEY_FRAMES = (JOURNEY_STEPS + 1) * JOURNEY_BLOCK;

/** Idle shimmer repeats a few times, then rests — no endless loop draining a cheap phone. */
const MAX_IDLE_LOOPS = 4;

export function clampJourneyLevel(done: number): number {
  return Math.max(0, Math.min(JOURNEY_STEPS, Math.round(done)));
}

/**
 * Shows every step already done, animates only the newest one, then lets the
 * current step shimmer. Returns a cleanup that detaches its listeners.
 */
export function playJourneyLevel(item: AnimationItem, done: number): () => void {
  const level: number = clampJourneyLevel(done);
  const arriveStart: number = level * JOURNEY_BLOCK;
  const arriveEnd: number = arriveStart + JOURNEY_ARRIVE;
  const idleEnd: number = arriveStart + JOURNEY_BLOCK;
  let phase: "arrive" | "idle" | "rest" = "arrive";
  let idleLoops = 0;

  function startIdle(): void {
    phase = "idle";
    item.setLoop(level < JOURNEY_STEPS);
    item.playSegments([arriveEnd, idleEnd], true);
  }

  const removeComplete: () => void = item.addEventListener("complete", () => {
    if (phase === "arrive") {
      startIdle();
    } else {
      phase = "rest";
    }
  });
  const removeLoop: () => void = item.addEventListener("loopComplete", () => {
    idleLoops += 1;
    if (idleLoops >= MAX_IDLE_LOOPS) {
      item.setLoop(false);
    }
  });

  item.setLoop(false);
  if (level === 0) {
    item.goToAndStop(arriveEnd, true);
    startIdle();
  } else {
    item.goToAndStop(arriveStart, true);
    item.playSegments([arriveStart, arriveEnd], true);
  }

  return () => {
    removeComplete();
    removeLoop();
  };
}
