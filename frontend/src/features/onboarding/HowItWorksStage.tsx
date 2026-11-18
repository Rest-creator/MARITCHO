"use client";

import { memo, type ReactNode } from "react";

import {
  CHAPTER_RESTS,
  SCENE_OBJECTS,
  sceneValuesAt,
  type SceneObjectKey,
  type SceneValues,
} from "@/features/onboarding/how-it-works-script";

type Props = {
  /** Receives each animated group so the parent can drive it imperatively. */
  register: (key: SceneObjectKey, node: SVGGElement | null) => void;
};

function toTransform(values: SceneValues): string {
  return `translate(${values.x} ${values.y}) scale(${values.scale})`;
}

/** Writes one frame of scene values straight to the DOM (no React render). */
export function applySceneValues(node: SVGGElement, values: SceneValues): void {
  node.setAttribute("transform", toTransform(values));
  node.style.opacity = String(Math.max(0, Math.min(1, values.opacity)));
  const fill: Element | null = node.querySelector("[data-fill]");
  if (fill !== null) {
    fill.setAttribute("transform", `scale(${Math.max(0, Math.min(1, values.fill))} 1)`);
  }
}

function starPath(outer: number, inner: number): string {
  const points: string[] = Array.from({ length: 10 }, (_, index) => {
    const radius: number = index % 2 === 0 ? outer : inner;
    const angle: number = (Math.PI / 5) * index - Math.PI / 2;
    return `${(Math.cos(angle) * radius).toFixed(2)},${(Math.sin(angle) * radius).toFixed(2)}`;
  });
  return `M${points.join(" L")} Z`;
}

const STAR: string = starPath(7, 3);

function Worker({ initial }: { initial: string }) {
  return (
    <>
      <circle r={14} className="hiw-worker" />
      <text className="hiw-worker__initial" textAnchor="middle" dy="0.35em">
        {initial}
      </text>
    </>
  );
}

function artFor(key: SceneObjectKey): ReactNode {
  switch (key) {
    case "jobCard":
      return (
        <>
          <rect x={-78} y={-26} width={156} height={52} rx={12} className="hiw-card" />
          <circle cx={-52} r={14} className="hiw-card__icon" />
          <path
            d="M-52,-8 C-48,-3 -46,0 -46,3 A6,6 0 0 1 -58,3 C-58,0 -56,-3 -52,-8 Z"
            className="hiw-card__drop"
          />
          <text x={-30} y={-3} className="hiw-card__title">
            Geyser leaking
          </text>
          <text x={-30} y={13} className="hiw-card__meta">
            Hillside · photo added
          </text>
        </>
      );
    case "pin":
      return (
        <>
          <ellipse cy={13} rx={9} ry={3} className="hiw-shadow" />
          <path
            d="M0,12 C0,12 -13,0 -13,-9 C-13,-16 -7,-22 0,-22 C7,-22 13,-16 13,-9 C13,0 0,12 0,12 Z"
            className="hiw-pin"
          />
          <circle cy={-9} r={4.5} className="hiw-pin__dot" />
        </>
      );
    case "workerA":
      return <Worker initial="T" />;
    case "workerB":
      return <Worker initial="N" />;
    case "workerC":
      return <Worker initial="S" />;
    case "quote":
      return (
        <>
          <path
            d="M-36,-13 H36 A6,6 0 0 1 42,-7 V7 A6,6 0 0 1 36,13 H-4 L-10,20 L-12,13 H-36 A6,6 0 0 1 -42,7 V-7 A6,6 0 0 1 -36,-13 Z"
            className="hiw-quote"
          />
          <text textAnchor="middle" dy="0.35em" className="hiw-quote__text">
            $25 · today
          </text>
        </>
      );
    case "progress":
      return (
        <>
          <rect x={-100} y={-3} width={200} height={6} rx={3} className="hiw-track" />
          <g transform="translate(-100 0)">
            <rect
              data-fill=""
              y={-3}
              width={200}
              height={6}
              rx={3}
              transform="scale(0 1)"
              className="hiw-fill"
            />
          </g>
          <text y={15} textAnchor="middle" className="hiw-track__labels">
            Hired · Arrived · Working · Done
          </text>
        </>
      );
    case "badge":
      return (
        <>
          <circle r={26} className="hiw-badge" />
          <polyline points="-11,1 -3,9 12,-8" className="hiw-badge__tick" />
        </>
      );
    case "stars":
      return (
        <>
          {[-36, -18, 0, 18, 36].map((x) => (
            <path key={x} d={STAR} transform={`translate(${x} 0)`} className="hiw-star" />
          ))}
        </>
      );
  }
}

/**
 * The illustration. Rendered once (memoised, stable props): every later
 * change is written by `applySceneValues`, whether Theatre is tweening it or
 * the static fallback is jumping between chapters.
 */
export const HowItWorksStage = memo(function HowItWorksStage({ register }: Props) {
  const firstRest: number = CHAPTER_RESTS[0] ?? 0;
  return (
    <svg viewBox="0 0 320 168" className="hiw-stage__svg" aria-hidden="true" focusable="false">
      {SCENE_OBJECTS.map((key) => {
        const start: SceneValues = sceneValuesAt(key, firstRest);
        return (
          <g
            key={key}
            ref={(node) => register(key, node)}
            transform={toTransform(start)}
            style={{ opacity: start.opacity }}
          >
            {artFor(key)}
          </g>
        );
      })}
    </svg>
  );
});
