"use client";

import { useEffect, useRef } from "react";

import type { LottieAnimation } from "@/core/motion/lottie-builders";
import { useCanAnimate } from "@/core/motion/use-can-animate";
import { useLottie } from "@/core/motion/use-lottie";
import {
  JOURNEY_STEPS,
  clampJourneyLevel,
  playJourneyLevel,
} from "@/features/jobs/animations/job-journey-timeline";

type Props = {
  /** Tracking steps already done, from `completedSteps(job.status)`. */
  done: number;
};

async function loadJobJourney(): Promise<LottieAnimation> {
  const animation = await import("@/features/jobs/animations/job-journey-animation");
  return animation.buildJobJourneyAnimation();
}

/**
 * The progress bars above the stepper labels. Static CSS bars render first
 * (and stay, with reduced motion or Data Saver); once the Lottie player has
 * loaded it takes over, filling the newest step and shimmering the current one.
 * Purely decorative — the labelled `<ol>` beside it carries the meaning.
 */
export function JobJourney({ done }: Props) {
  const level: number = clampJourneyLevel(done);
  const canAnimate: boolean = useCanAnimate();
  const containerRef = useRef<HTMLDivElement>(null);
  const item = useLottie(containerRef, loadJobJourney, canAnimate);

  useEffect(() => {
    if (item === null) return undefined;
    return playJourneyLevel(item, level);
  }, [item, level]);

  return (
    <div className="journey" aria-hidden="true" data-animated={item !== null}>
      {item === null && (
        <div className="journey__static">
          {Array.from({ length: JOURNEY_STEPS }, (_, step) => (
            <span
              key={step}
              className={`stepper__bar ${step < level ? "stepper__bar--done" : ""} ${step === level ? "stepper__bar--current" : ""}`}
            />
          ))}
        </div>
      )}
      <div ref={containerRef} className="journey__lottie" />
    </div>
  );
}
