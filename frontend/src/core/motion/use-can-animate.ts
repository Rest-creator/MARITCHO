"use client";

import { useSyncExternalStore } from "react";

const REDUCED_MOTION_QUERY = "(prefers-reduced-motion: reduce)";

type ConnectionHint = { saveData?: boolean };

/**
 * Decorative motion is opt-out on the worker's worst day: no animation when
 * the phone asks for reduced motion, when Data Saver is on (the player is an
 * extra ~50 KB), or where the browser can't tell us (SSR, old WebViews).
 */
function readCanAnimate(): boolean {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return false;
  }
  if (window.matchMedia(REDUCED_MOTION_QUERY).matches) {
    return false;
  }
  const connection: ConnectionHint | undefined = (
    navigator as Navigator & { connection?: ConnectionHint }
  ).connection;
  return connection?.saveData !== true;
}

function subscribe(onChange: () => void): () => void {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return () => undefined;
  }
  const query: MediaQueryList = window.matchMedia(REDUCED_MOTION_QUERY);
  query.addEventListener("change", onChange);
  return () => query.removeEventListener("change", onChange);
}

function readServerSnapshot(): boolean {
  return false;
}

/** True when decorative Lottie motion may load and play. Static on the server. */
export function useCanAnimate(): boolean {
  return useSyncExternalStore(subscribe, readCanAnimate, readServerSnapshot);
}
