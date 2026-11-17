"use client";

import { useEffect, useState, type RefObject } from "react";
import type { AnimationItem } from "lottie-web";

import type { LottieAnimation } from "@/core/motion/lottie-builders";

/**
 * Lazily loads the SVG-only Lottie player and one animation into `container`.
 *
 * Both arrive as separate content-hashed chunks, so they cost nothing until a
 * screen actually animates, and the service worker serves them offline after
 * the first view. Any failure leaves `null` and the caller keeps its static UI.
 * `loadAnimation` must be a stable (module-level) function.
 */
export function useLottie(
  container: RefObject<HTMLElement | null>,
  loadAnimation: () => Promise<LottieAnimation>,
  enabled: boolean,
): AnimationItem | null {
  const [item, setItem] = useState<AnimationItem | null>(null);

  useEffect(() => {
    if (!enabled) return undefined;
    let isCancelled = false;
    let loaded: AnimationItem | null = null;

    Promise.all([import("lottie-web/build/player/lottie_light"), loadAnimation()])
      .then(([player, animationData]) => {
        const target: HTMLElement | null = container.current;
        if (isCancelled || target === null) return;
        loaded = player.default.loadAnimation({
          container: target,
          renderer: "svg",
          loop: false,
          autoplay: false,
          animationData,
          rendererSettings: { preserveAspectRatio: "xMidYMid meet", progressiveLoad: true },
        });
        setItem(loaded);
      })
      .catch(() => {
        // Decorative only: a failed chunk download keeps the static fallback.
      });

    return () => {
      isCancelled = true;
      loaded?.destroy();
      setItem(null);
    };
  }, [container, loadAnimation, enabled]);

  return item;
}
