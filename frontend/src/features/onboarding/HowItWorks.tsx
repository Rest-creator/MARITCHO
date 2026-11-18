"use client";

import { useCallback, useEffect, useRef, useState, type PointerEvent } from "react";
import type { ISequence } from "@theatre/core";

import { Icon } from "@/components/ui/Icon";
import { useCanAnimate } from "@/core/motion/use-can-animate";
import {
  CHAPTERS,
  SCENE_OBJECTS,
  SEQUENCE_LENGTH,
  chapterProgress,
  clampChapter,
  restFor,
  sceneValuesAt,
  type SceneObjectKey,
} from "@/features/onboarding/how-it-works-script";
import type { HowItWorksRuntime } from "@/features/onboarding/how-it-works-theatre";
import { HowItWorksStage, applySceneValues } from "@/features/onboarding/HowItWorksStage";
import { loadHowItWorks } from "@/features/onboarding/load-how-it-works";

/** Pause on each chapter during the one-time automatic tour. */
const AUTO_ADVANCE_MS = 2600;
/** Seconds of the sequence scrubbed by dragging across the full stage. */
const SCRUB_SECONDS_PER_WIDTH = 1.8;
/** Seconds between two chapter rests, for scaling jump playback speed. */
const CHAPTER_SECONDS = 1.2;
const SWIPE_THRESHOLD_PX = 36;

type Drag = {
  pointerId: number;
  startX: number;
  startPosition: number;
  startChapter: number;
  width: number;
};

/**
 * "How Maritcho works": four chapters on one animated scene. Swipe or drag the
 * scene to scrub through it, or use Back/Next and the dots. Theatre.js (~20 KB)
 * only loads once the card is near the screen and motion is allowed;
 * otherwise the same scene and captions step through without tweening.
 */
export function HowItWorks() {
  const canAnimate: boolean = useCanAnimate();
  const [chapter, setChapter] = useState<number>(0);
  const [isNearViewport, setIsNearViewport] = useState<boolean>(
    () => typeof IntersectionObserver === "undefined",
  );
  const [runtime, setRuntime] = useState<HowItWorksRuntime | null>(null);
  const live: HowItWorksRuntime | null = canAnimate ? runtime : null;

  const sectionRef = useRef<HTMLElement>(null);
  const nodesRef = useRef<Partial<Record<SceneObjectKey, SVGGElement>>>({});
  const chapterRef = useRef<number>(0);
  const hasInteractedRef = useRef<boolean>(false);
  const dragRef = useRef<Drag | null>(null);
  const sequenceRef = useRef<ISequence | null>(null);

  const register = useCallback((key: SceneObjectKey, node: SVGGElement | null): void => {
    if (node === null) {
      delete nodesRef.current[key];
    } else {
      nodesRef.current[key] = node;
    }
  }, []);

  const showChapter = useCallback((next: number): void => {
    chapterRef.current = next;
    setChapter(next);
  }, []);

  // Fetch nothing until the card is about to be seen.
  useEffect(() => {
    const section: HTMLElement | null = sectionRef.current;
    if (!canAnimate || isNearViewport || section === null) return undefined;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setIsNearViewport(true);
          observer.disconnect();
        }
      },
      { rootMargin: "200px" },
    );
    observer.observe(section);
    return () => observer.disconnect();
  }, [canAnimate, isNearViewport]);

  useEffect(() => {
    if (!canAnimate || !isNearViewport) return undefined;
    let isCancelled = false;
    loadHowItWorks()
      .then((loaded) => {
        if (!isCancelled) setRuntime(loaded);
      })
      .catch(() => {
        // Decorative: a failed download keeps the static steps working.
      });
    return () => {
      isCancelled = true;
    };
  }, [canAnimate, isNearViewport]);

  // Theatre drives the scene frame by frame, straight to the DOM.
  useEffect(() => {
    if (live === null) return undefined;
    const unsubscribers: (() => void)[] = SCENE_OBJECTS.map((key) =>
      live.objects[key].onValuesChange((values) => {
        const node: SVGGElement | undefined = nodesRef.current[key];
        if (node !== undefined) applySceneValues(node, values);
      }),
    );
    return () => unsubscribers.forEach((unsubscribe) => unsubscribe());
  }, [live]);

  // Without Theatre: jump to each chapter's resting pose.
  useEffect(() => {
    if (live !== null) return;
    for (const key of SCENE_OBJECTS) {
      const node: SVGGElement | undefined = nodesRef.current[key];
      if (node !== undefined) applySceneValues(node, sceneValuesAt(key, restFor(chapter)));
    }
  }, [live, chapter]);

  /*
   * Theatre's playhead is imperative (`sequence.position = …`, `play()`), so
   * handlers and the tour reach it through a ref rather than mutating an
   * object held in React state.
   */
  useEffect(() => {
    sequenceRef.current = live === null ? null : live.sheet.sequence;
  }, [live]);

  // One automatic walk-through, abandoned the moment the user takes over.
  useEffect(() => {
    const current: ISequence | null = sequenceRef.current;
    if (live === null || current === null) return undefined;
    const sequence: ISequence = current;
    let isCancelled = false;
    let timer: number | undefined;

    const wait = (ms: number): Promise<void> =>
      new Promise((resolve) => {
        timer = window.setTimeout(resolve, ms);
      });
    const play = (from: number, to: number): Promise<boolean> =>
      sequence.play({ range: [from, to] }).catch(() => false);

    async function tour(): Promise<void> {
      if (hasInteractedRef.current) {
        sequence.position = restFor(chapterRef.current);
        return;
      }
      sequence.position = 0;
      if (!(await play(0, restFor(0)))) return;
      for (let next = 1; next < CHAPTERS.length; next += 1) {
        await wait(AUTO_ADVANCE_MS);
        if (isCancelled || hasInteractedRef.current) return;
        showChapter(next);
        if (!(await play(restFor(next - 1), restFor(next)))) return;
      }
    }

    void tour();
    return () => {
      isCancelled = true;
      window.clearTimeout(timer);
      sequence.pause();
    };
  }, [live, showChapter]);

  function goTo(target: number): void {
    hasInteractedRef.current = true;
    const next: number = clampChapter(target);
    showChapter(next);
    const sequence: ISequence | null = sequenceRef.current;
    if (sequence === null) return;

    sequence.pause();
    const from: number = sequence.position;
    const to: number = restFor(next);
    const distance: number = Math.abs(to - from);
    if (distance < 0.01) {
      sequence.position = to;
      return;
    }
    // Long jumps play faster; rewinding is brisker than playing forward.
    const rate: number = Math.max(1, distance / CHAPTER_SECONDS) * (to < from ? 1.6 : 1);
    void sequence
      .play(
        to > from ? { range: [from, to], rate } : { range: [to, from], direction: "reverse", rate },
      )
      .catch(() => false);
  }

  function handlePointerDown(event: PointerEvent<HTMLDivElement>): void {
    if (event.pointerType === "mouse" && event.button !== 0) return;
    hasInteractedRef.current = true;
    const sequence: ISequence | null = sequenceRef.current;
    sequence?.pause();
    dragRef.current = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startPosition: sequence !== null ? sequence.position : restFor(chapterRef.current),
      startChapter: chapterRef.current,
      width: Math.max(1, event.currentTarget.clientWidth),
    };
    // Keeps the drag alive if the finger leaves the stage (absent on some old WebViews).
    if (typeof event.currentTarget.setPointerCapture === "function") {
      event.currentTarget.setPointerCapture(event.pointerId);
    }
  }

  function handlePointerMove(event: PointerEvent<HTMLDivElement>): void {
    const drag: Drag | null = dragRef.current;
    const sequence: ISequence | null = sequenceRef.current;
    if (drag === null || drag.pointerId !== event.pointerId || sequence === null) return;
    const deltaX: number = event.clientX - drag.startX;
    const position: number = Math.max(
      0,
      Math.min(
        SEQUENCE_LENGTH,
        drag.startPosition - (deltaX / drag.width) * SCRUB_SECONDS_PER_WIDTH,
      ),
    );
    sequence.position = position;
    const nearest: number = Math.round(chapterProgress(position));
    if (nearest !== chapterRef.current) showChapter(nearest);
  }

  function handlePointerEnd(event: PointerEvent<HTMLDivElement>): void {
    const drag: Drag | null = dragRef.current;
    if (drag === null || drag.pointerId !== event.pointerId) return;
    dragRef.current = null;
    const deltaX: number = event.clientX - drag.startX;
    const isSwipe: boolean = Math.abs(deltaX) >= SWIPE_THRESHOLD_PX;

    const sequence: ISequence | null = sequenceRef.current;
    if (sequence === null) {
      if (isSwipe) goTo(drag.startChapter + (deltaX < 0 ? 1 : -1));
      return;
    }
    // Settle on a chapter, leaning the way the finger was moving.
    const progress: number = chapterProgress(sequence.position);
    goTo(
      !isSwipe
        ? Math.round(progress)
        : deltaX < 0
          ? Math.ceil(progress - 0.15)
          : Math.floor(progress + 0.15),
    );
  }

  const current = CHAPTERS[chapter] ?? CHAPTERS[0];
  const lastChapter: number = CHAPTERS.length - 1;

  return (
    <section ref={sectionRef} className="card stack hiw" aria-labelledby="hiw-title">
      <div className="row row--between">
        <h2 id="hiw-title" className="hiw__title">
          How Maritcho works
        </h2>
        <span className="meta">
          {chapter + 1} of {CHAPTERS.length}
        </span>
      </div>

      <div
        className="hiw-stage"
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerEnd}
        onPointerCancel={handlePointerEnd}
      >
        <HowItWorksStage register={register} />
      </div>

      <div className="hiw-caption" aria-live="polite">
        <div className="hiw-caption__title">{current?.title}</div>
        <p className="meta meta--secondary hiw-caption__text">{current?.caption}</p>
      </div>

      <div className="row row--between">
        <button
          type="button"
          className="btn btn--sm btn--ghost"
          disabled={chapter === 0}
          onClick={() => goTo(chapter - 1)}
        >
          <Icon name="back" size={16} />
          Back
        </button>
        <div className="hiw-dots" role="group" aria-label="Choose a step">
          {CHAPTERS.map((item, index) => (
            <button
              key={item.title}
              type="button"
              className="hiw-dot"
              aria-label={`Step ${index + 1}: ${item.title}`}
              aria-current={index === chapter ? "step" : undefined}
              onClick={() => goTo(index)}
            />
          ))}
        </div>
        <button
          type="button"
          className="btn btn--sm btn--soft"
          disabled={chapter === lastChapter}
          onClick={() => goTo(chapter + 1)}
        >
          Next
          <Icon name="chevronRight" size={16} />
        </button>
      </div>
    </section>
  );
}
