import type { ReactNode } from "react";

/** Background glow arrangements used across the app UI. */
export type GlowPreset = "employer" | "worker" | "plain";

const GLOWS: Record<GlowPreset, readonly string[]> = {
  employer: [
    "glow--amber glow--top-left",
    "glow--moss glow--mid-right",
    "glow--slate glow--bottom",
  ],
  worker: ["glow--moss glow--top-right", "glow--amber glow--mid-left", "glow--slate glow--bottom"],
  plain: ["glow--slate glow--bottom"],
};

type Props = {
  children: ReactNode;
  glow?: GlowPreset;
  /** Applies the body padding/stack layout; turn off for custom layouts (chat, profile). */
  isPadded?: boolean;
  hasTabBar?: boolean;
  bodyClassName?: string;
};

export function Screen({
  children,
  glow = "employer",
  isPadded = true,
  hasTabBar = false,
  bodyClassName,
}: Props) {
  const bodyClasses = ["screen__body", hasTabBar ? "screen__body--nav" : "", bodyClassName ?? ""]
    .filter(Boolean)
    .join(" ");

  return (
    <div className="screen">
      <div className="screen__glows" aria-hidden="true">
        {GLOWS[glow].map((classes) => (
          <div key={classes} className={`glow ${classes}`} />
        ))}
      </div>
      {isPadded ? <main className={bodyClasses}>{children}</main> : children}
    </div>
  );
}
