import type { AnimationItem } from "lottie-web";
import { describe, expect, it, vi } from "vitest";

import {
  JOURNEY_ARRIVE,
  JOURNEY_BLOCK,
  clampJourneyLevel,
  playJourneyLevel,
} from "@/features/jobs/animations/job-journey-timeline";

type Listener = () => void;

function fakeItem() {
  const listeners = new Map<string, Listener[]>();
  const calls = {
    goToAndStop: vi.fn(),
    playSegments: vi.fn(),
    setLoop: vi.fn(),
  };
  const item = {
    ...calls,
    addEventListener: (name: string, callback: Listener): (() => void) => {
      listeners.set(name, [...(listeners.get(name) ?? []), callback]);
      return () =>
        listeners.set(
          name,
          (listeners.get(name) ?? []).filter((listener) => listener !== callback),
        );
    },
  } as unknown as AnimationItem;
  const emit = (name: string): void => (listeners.get(name) ?? []).forEach((fn) => fn());
  const listenerCount = (): number =>
    [...listeners.values()].reduce((sum, list) => sum + list.length, 0);
  return { item, calls, emit, listenerCount };
}

describe("playJourneyLevel", () => {
  it("draws earlier steps instantly and animates only the newest one", () => {
    const { item, calls } = fakeItem();
    playJourneyLevel(item, 2);

    expect(calls.goToAndStop).toHaveBeenCalledWith(2 * JOURNEY_BLOCK, true);
    expect(calls.playSegments).toHaveBeenCalledWith(
      [2 * JOURNEY_BLOCK, 2 * JOURNEY_BLOCK + JOURNEY_ARRIVE],
      true,
    );
  });

  it("moves to a looping shimmer after arriving, then rests after a few loops", () => {
    const { item, calls, emit } = fakeItem();
    playJourneyLevel(item, 1);

    emit("complete");
    expect(calls.setLoop).toHaveBeenLastCalledWith(true);
    expect(calls.playSegments).toHaveBeenLastCalledWith(
      [JOURNEY_BLOCK + JOURNEY_ARRIVE, 2 * JOURNEY_BLOCK],
      true,
    );

    emit("loopComplete");
    emit("loopComplete");
    emit("loopComplete");
    expect(calls.setLoop).toHaveBeenLastCalledWith(true);
    emit("loopComplete");
    expect(calls.setLoop).toHaveBeenLastCalledWith(false);

    // The final pass completing must not restart the shimmer.
    const segmentCalls: number = calls.playSegments.mock.calls.length;
    emit("complete");
    expect(calls.playSegments.mock.calls.length).toBe(segmentCalls);
  });

  it("skips the empty arrival for a job that is only requested", () => {
    const { item, calls } = fakeItem();
    playJourneyLevel(item, 0);

    expect(calls.goToAndStop).toHaveBeenCalledWith(JOURNEY_ARRIVE, true);
    expect(calls.playSegments).toHaveBeenCalledTimes(1);
    expect(calls.playSegments).toHaveBeenCalledWith([JOURNEY_ARRIVE, JOURNEY_BLOCK], true);
  });

  it("plays the signed-off finish once, without looping", () => {
    const { item, calls, emit } = fakeItem();
    playJourneyLevel(item, 4);
    emit("complete");

    expect(calls.setLoop).toHaveBeenLastCalledWith(false);
    expect(calls.playSegments).toHaveBeenLastCalledWith(
      [4 * JOURNEY_BLOCK + JOURNEY_ARRIVE, 5 * JOURNEY_BLOCK],
      true,
    );
  });

  it("detaches its listeners on cleanup", () => {
    const { item, listenerCount } = fakeItem();
    const cleanup = playJourneyLevel(item, 3);
    expect(listenerCount()).toBe(2);
    cleanup();
    expect(listenerCount()).toBe(0);
  });

  it("clamps out-of-range levels", () => {
    expect(clampJourneyLevel(-1)).toBe(0);
    expect(clampJourneyLevel(9)).toBe(4);
  });
});
