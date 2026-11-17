import { describe, expect, it } from "vitest";

import { buildTheatreState, valueAt } from "@/core/motion/theatre-state";

describe("buildTheatreState", () => {
  const state = buildTheatreState({
    sheetId: "Sheet",
    length: 2,
    objects: {
      box: {
        x: [
          [0, 10],
          [1, 50],
          [2, 20],
        ],
        y: [],
      },
    },
  });

  it("matches the Theatre 0.7 on-disk project format", () => {
    expect(state.definitionVersion).toBe("0.4.0");
    const sequence = state.sheetsById.Sheet?.sequence;
    expect(sequence).toMatchObject({ type: "PositionalSequence", length: 2, subUnitsPerUnit: 30 });
    expect(sequence?.tracksByObject.box?.trackIdByPropPath).toEqual({ '["x"]': "box.x" });
  });

  it("connects every keyframe to the next except the last, with ease-out handles", () => {
    const keyframes =
      state.sheetsById.Sheet?.sequence.tracksByObject.box?.trackData["box.x"]?.keyframes;
    expect(keyframes?.map((keyframe) => keyframe.connectedRight)).toEqual([true, true, false]);
    expect(keyframes?.map((keyframe) => keyframe.value)).toEqual([10, 50, 20]);
    // Segment curve = cubic-bezier(left[2], left[3], right[0], right[1]) = (0.2, 0.8, 0.2, 1).
    expect(keyframes?.[0]?.handles.slice(2)).toEqual([0.2, 0.8]);
    expect(keyframes?.[1]?.handles.slice(0, 2)).toEqual([0.2, 1]);
  });

  it("skips empty tracks", () => {
    expect(state.sheetsById.Sheet?.sequence.tracksByObject.box?.trackData["box.y"]).toBeUndefined();
  });
});

describe("valueAt", () => {
  const track = [
    [1, 0],
    [3, 100],
  ] as const;

  it("holds outside the keyframes and interpolates between them", () => {
    expect(valueAt(track, 0, 7)).toBe(0);
    expect(valueAt(track, 2, 7)).toBe(50);
    expect(valueAt(track, 9, 7)).toBe(100);
  });

  it("uses the fallback when a prop has no track", () => {
    expect(valueAt(undefined, 2, 7)).toBe(7);
    expect(valueAt([], 2, 7)).toBe(7);
  });
});
