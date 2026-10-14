import { defineConfig } from "@playwright/test";

/*
 * Two suites, both on a small Android-sized screen (the phones Maricho is
 * built for):
 *
 * - `lifecycle` drives the real stack: this Next.js app in front of the
 *   docker-compose FastAPI backend. `npm run test:e2e` starts a throwaway
 *   backend for it and points the build at it (e2e/run-lifecycle.mjs).
 * - `visual` screenshots every screen with the API stubbed in the browser,
 *   so nothing (clock, ids, other people's data) can shift a pixel. Font
 *   rendering differs per OS, so baselines are made and checked in the
 *   Playwright Linux image: `npm run test:visual` (Docker) and CI.
 *
 * Set E2E_BASE_URL to test an app that is already running elsewhere;
 * otherwise a production build is served on port 3100.
 */

const PORT = 3100;
const externalBaseUrl = process.env.E2E_BASE_URL;
const baseURL = externalBaseUrl ?? `http://127.0.0.1:${PORT}`;

const phone = {
  viewport: { width: 360, height: 780 },
  deviceScaleFactor: 2,
  isMobile: true,
  hasTouch: true,
  locale: "en-GB",
  timezoneId: "Africa/Harare",
  colorScheme: "dark" as const,
};

export default defineConfig({
  testDir: "./e2e",
  outputDir: "./e2e/.results",
  snapshotPathTemplate: "{testDir}/{testFileDir}/__screenshots__/{arg}{ext}",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  timeout: 60_000,
  expect: {
    timeout: 10_000,
    toHaveScreenshot: { animations: "disabled", caret: "hide", maxDiffPixelRatio: 0.002 },
  },
  use: {
    baseURL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "lifecycle",
      testMatch: "lifecycle/**/*.spec.ts",
      // One long story; its steps depend on each other.
      fullyParallel: false,
      timeout: 180_000,
      use: phone,
    },
    {
      name: "visual",
      testMatch: "visual/**/*.spec.ts",
      // A service worker would answer requests before the API stubs could.
      use: { ...phone, serviceWorkers: "block" },
    },
  ],
  webServer: externalBaseUrl
    ? undefined
    : {
        command: `npm run build && npm run start -- --hostname 127.0.0.1 --port ${PORT}`,
        url: baseURL,
        // Never reuse: the build bakes in which backend the chat socket uses.
        reuseExistingServer: false,
        timeout: 300_000,
      },
});
