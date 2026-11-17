import { describe, expect, it } from "vitest";

import {
  CELEBRATION_FRAMES,
  buildCelebrationAnimation,
} from "@/components/ui/animations/celebration-animation";
import type { LottieAnimation, Prop, ShapeItem } from "@/core/motion/lottie-builders";
import { buildJobJourneyAnimation } from "@/features/jobs/animations/job-journey-animation";
import {
  JOURNEY_ARRIVE,
  JOURNEY_BLOCK,
  JOURNEY_FRAMES,
} from "@/features/jobs/animations/job-journey-timeline";

function propsOf(item: ShapeItem): Prop[] {
  switch (item.ty) {
    case "gr":
      return item.it.flatMap(propsOf);
    case "el":
      return [item.p, item.s];
    case "sh":
      return [];
    case "fl":
      return [item.c, item.o];
    case "st":
      return [item.c, item.o, item.w];
    case "tm":
      return [item.s, item.e, item.o];
    case "tr":
      return [item.p, item.a, item.s, item.r, item.o, item.sk, item.sa];
  }
}

function allProps(animation: LottieAnimation): Prop[] {
  return animation.layers.flatMap((layer) => [
    layer.ks.o,
    layer.ks.r,
    layer.ks.p,
    layer.ks.a,
    layer.ks.s,
    ...layer.shapes.flatMap(propsOf),
  ]);
}

function expectWellFormed(animation: LottieAnimation, totalFrames: number): void {
  expect(animation.op).toBe(totalFrames);
  expect(animation.fr).toBe(30);
  animation.layers.forEach((layer, index) => {
    expect(layer.ind).toBe(index + 1);
    expect(layer.ip).toBeGreaterThanOrEqual(0);
    expect(layer.ip).toBeLessThan(layer.op);
    expect(layer.op).toBeLessThanOrEqual(totalFrames);
  });
  for (const prop of allProps(animation)) {
    if (prop.a === 0) continue;
    const frames: number[] = prop.k.map((keyframe) => keyframe.t);
    expect(frames).toEqual([...frames].sort((a, b) => a - b));
    expect(new Set(frames).size).toBe(frames.length);
    expect(Math.max(...frames)).toBeLessThanOrEqual(totalFrames);
    // Every segment but the last carries its easing.
    prop.k.slice(0, -1).forEach((keyframe) => expect(keyframe.o).toBeDefined());
  }
  // Valid JSON round-trip: exactly what an After Effects export would be.
  expect(JSON.parse(JSON.stringify(animation))).toEqual(animation);
}

describe("job journey animation", () => {
  const animation: LottieAnimation = buildJobJourneyAnimation();

  it("is a well-formed Lottie composition", () => {
    expectWellFormed(animation, JOURNEY_FRAMES);
    expect(animation.w).toBe(320);
    expect(animation.h).toBe(12);
  });

  it("names an arrive and an idle marker for every level, matching the timeline", () => {
    expect(animation.markers.map((marker) => marker.cm)).toEqual([
      "level-0-arrive",
      "level-0-idle",
      "level-1-arrive",
      "level-1-idle",
      "level-2-arrive",
      "level-2-idle",
      "level-3-arrive",
      "level-3-idle",
      "level-4-arrive",
      "level-4-idle",
    ]);
    const idle = animation.markers.find((marker) => marker.cm === "level-2-idle");
    expect(idle).toEqual({
      tm: 2 * JOURNEY_BLOCK + JOURNEY_ARRIVE,
      dr: JOURNEY_BLOCK - JOURNEY_ARRIVE,
      cm: "level-2-idle",
    });
  });

  it("stays a few KB so it costs almost nothing on a data bundle", () => {
    expect(JSON.stringify(animation).length).toBeLessThan(30_000);
  });
});

describe("celebration animation", () => {
  it("is a well-formed, small Lottie composition", () => {
    const animation: LottieAnimation = buildCelebrationAnimation();
    expectWellFormed(animation, CELEBRATION_FRAMES);
    expect(animation.markers.map((marker) => marker.cm)).toEqual(["burst", "settle"]);
    expect(JSON.stringify(animation).length).toBeLessThan(30_000);
  });
});
