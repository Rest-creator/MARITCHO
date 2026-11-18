import { describe, expect, it } from "vitest";

import {
  CHAPTERS,
  CHAPTER_RESTS,
  SCENE_OBJECTS,
  SCENE_SCRIPT,
  SEQUENCE_LENGTH,
  buildHowItWorksState,
  chapterProgress,
  restFor,
  sceneValuesAt,
  type SceneObjectKey,
} from "@/features/onboarding/how-it-works-script";

function visibleAt(seconds: number): SceneObjectKey[] {
  return SCENE_OBJECTS.filter((key) => sceneValuesAt(key, seconds).opacity > 0.5);
}

describe("how-it-works script", () => {
  it("has one rest per chapter, in order, ending the sequence", () => {
    expect(CHAPTER_RESTS).toHaveLength(CHAPTERS.length);
    expect([...CHAPTER_RESTS]).toEqual([...CHAPTER_RESTS].sort((a, b) => a - b));
    expect(CHAPTER_RESTS[CHAPTER_RESTS.length - 1]).toBe(SEQUENCE_LENGTH);
  });

  it("keeps every keyframe ordered and inside the sequence", () => {
    for (const key of SCENE_OBJECTS) {
      for (const track of Object.values(SCENE_SCRIPT[key].tracks)) {
        const times: number[] = (track ?? []).map(([seconds]) => seconds);
        expect(times).toEqual([...times].sort((a, b) => a - b));
        expect(new Set(times).size).toBe(times.length);
        expect(Math.max(...times)).toBeLessThanOrEqual(SEQUENCE_LENGTH);
      }
    }
  });

  it("tells the story chapter by chapter in the static poses", () => {
    expect(visibleAt(restFor(0))).toEqual(["jobCard"]);
    expect(visibleAt(restFor(1))).toEqual([
      "jobCard",
      "pin",
      "workerA",
      "workerB",
      "workerC",
      "quote",
    ]);
    expect(visibleAt(restFor(2))).toEqual(["jobCard", "pin", "workerB", "progress"]);
    expect(visibleAt(restFor(3))).toEqual(["progress", "badge", "stars"]);
  });

  it("moves the hired worker to the job and fills progress as the job is done", () => {
    expect(sceneValuesAt("workerB", restFor(1)).x).toBe(252);
    expect(sceneValuesAt("workerB", restFor(2)).x).toBe(140);
    expect(sceneValuesAt("progress", restFor(2)).fill).toBe(0.75);
    expect(sceneValuesAt("progress", restFor(3)).fill).toBe(1);
  });

  it("maps sequence positions to fractional chapters", () => {
    expect(chapterProgress(0)).toBe(0);
    expect(chapterProgress(restFor(2))).toBe(2);
    expect(chapterProgress((restFor(1) + restFor(2)) / 2)).toBeCloseTo(1.5);
    expect(chapterProgress(99)).toBe(3);
  });

  it("builds Theatre state with a track for every scripted prop", () => {
    const sequence = buildHowItWorksState().sheetsById["How it works"]?.sequence;
    expect(sequence?.length).toBe(SEQUENCE_LENGTH);
    for (const key of SCENE_OBJECTS) {
      const scripted: string[] = Object.keys(SCENE_SCRIPT[key].tracks).map((prop) =>
        JSON.stringify([prop]),
      );
      expect(Object.keys(sequence?.tracksByObject[key]?.trackIdByPropPath ?? {})).toEqual(scripted);
    }
  });
});
