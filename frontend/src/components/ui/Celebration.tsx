"use client";

import { useCallback, useEffect, useRef } from "react";

import { Icon } from "@/components/ui/Icon";
import type { LottieAnimation } from "@/core/motion/lottie-builders";
import { useCanAnimate } from "@/core/motion/use-can-animate";
import { useLottie } from "@/core/motion/use-lottie";

type Props = {
  title: string;
  detail: string;
  /** Called once: on tap, or automatically after a few seconds. */
  onDone: () => void;
};

const AUTO_DISMISS_MS = 3600;

async function loadCelebration(): Promise<LottieAnimation> {
  const animation = await import("@/components/ui/animations/celebration-animation");
  return animation.buildCelebrationAnimation();
}

/**
 * A small non-blocking toast for real milestones (tier unlocked, job signed
 * off). It never covers the screen or holds up a tap. Without motion it shows
 * the same message with a static badge.
 */
export function Celebration({ title, detail, onDone }: Props) {
  const canAnimate: boolean = useCanAnimate();
  const containerRef = useRef<HTMLSpanElement>(null);
  const item = useLottie(containerRef, loadCelebration, canAnimate);
  const onDoneRef = useRef<() => void>(onDone);
  const hasFinishedRef = useRef<boolean>(false);

  useEffect(() => {
    onDoneRef.current = onDone;
  }, [onDone]);

  const finish = useCallback((): void => {
    if (hasFinishedRef.current) return;
    hasFinishedRef.current = true;
    onDoneRef.current();
  }, []);

  useEffect(() => {
    if (item === null) return;
    item.goToAndPlay(0, true);
  }, [item]);

  useEffect(() => {
    const timer: number = window.setTimeout(finish, AUTO_DISMISS_MS);
    return () => window.clearTimeout(timer);
  }, [finish]);

  return (
    <div className="celebration" role="status" aria-live="polite">
      <button type="button" className="celebration__card" onClick={finish}>
        <span className="celebration__art" aria-hidden="true">
          {!canAnimate && (
            <span className="celebration__badge">
              <Icon name="shieldCheck" size={30} strokeWidth={2.2} />
            </span>
          )}
          <span ref={containerRef} className="celebration__lottie" />
        </span>
        <span className="celebration__text">
          <span className="celebration__title">{title}</span>
          <span className="celebration__detail">{detail}</span>
        </span>
      </button>
    </div>
  );
}
