import type { HowItWorksRuntime } from "@/features/onboarding/how-it-works-theatre";

/**
 * Lazily loads Theatre.js core plus the onboarding sheet as one chunk.
 *
 * Designers: on a dev build, open the Welcome page with `?studio` to get
 * Theatre Studio on top of the live scene. Retime or reshape anything, then
 * export the project JSON and port the keyframes into `how-it-works-script.ts`.
 * The `NODE_ENV` check is replaced at build time, so production bundles never
 * include Studio.
 */
export async function loadHowItWorks(): Promise<HowItWorksRuntime> {
  if (
    process.env.NODE_ENV === "development" &&
    new URLSearchParams(window.location.search).has("studio")
  ) {
    const studio = await import("@theatre/studio");
    studio.default.initialize();
  }
  const theatre = await import("@/features/onboarding/how-it-works-theatre");
  const runtime: HowItWorksRuntime = theatre.getHowItWorksRuntime();
  await runtime.ready;
  return runtime;
}
