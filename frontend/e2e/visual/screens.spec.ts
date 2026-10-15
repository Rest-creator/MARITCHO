import { expect, test } from "@playwright/test";

import { EXPERT_ID, LIVE_JOB_ID, OPEN_JOB_ID, WORKER, stubWorld } from "./fixtures";

/*
 * One screenshot per designed screen. `ready` is something that only
 * appears once the screen has its data, so skeletons never get captured.
 */

type Screen = {
  name: string;
  path: string;
  who: "BUYER" | "WORKER" | null;
  ready: string;
};

const SCREENS: readonly Screen[] = [
  { name: "01-welcome", path: "/", who: null, ready: "Your skills are your CV." },
  { name: "02-sign-up", path: "/signup?role=buyer", who: null, ready: "Let's get you set up" },
  { name: "03-employer-home", path: "/employer", who: "BUYER", ready: "Popular near you" },
  { name: "04-post-job", path: "/employer/post?trade=PLUMBING", who: "BUYER", ready: "Post a job" },
  { name: "05-my-jobs", path: "/employer/jobs", who: "BUYER", ready: "Kitchen sink is leaking" },
  {
    name: "06-applicants",
    path: `/employer/jobs/${OPEN_JOB_ID}`,
    who: "BUYER",
    ready: "Expert plumber",
  },
  {
    name: "07-worker-profile",
    path: `/employer/jobs/${OPEN_JOB_ID}/workers/${EXPERT_ID}`,
    who: "BUYER",
    ready: "Expert plumber",
  },
  {
    name: "08-job-tracking",
    path: `/employer/jobs/${LIVE_JOB_ID}/track`,
    who: "BUYER",
    ready: "How did they do?",
  },
  { name: "09-chat", path: `/chat/${LIVE_JOB_ID}`, who: "BUYER", ready: "Okay, go ahead." },
  {
    name: "10-worker-skills",
    path: "/worker/skills",
    who: "WORKER",
    ready: "What work can you do?",
  },
  { name: "11-jobs-near-you", path: "/worker", who: "WORKER", ready: "Kitchen sink is leaking" },
  {
    name: "12-job-detail",
    path: "/worker/jobs/job-open-2",
    who: "WORKER",
    ready: "Plug points in the kitchen stopped working",
  },
  { name: "13-my-work", path: "/worker/work?tab=active", who: "WORKER", ready: "You got the job" },
];

for (const screen of SCREENS) {
  test(screen.name, async ({ page }) => {
    const unexpected = await stubWorld(page, screen.who);
    await page.goto(screen.path);
    await expect(page.getByText(screen.ready).first()).toBeVisible();
    // Late answers (e.g. "can this phone send photos?") still change the screen.
    await page.waitForLoadState("networkidle");
    await page.evaluate(() => document.fonts.ready);
    await expect(page).toHaveScreenshot(`${screen.name}.png`);
    expect(unexpected, "API calls with no fixture").toEqual([]);
  });
}

test("02b-sign-in-code", async ({ page }) => {
  const unexpected = await stubWorld(page, null);
  await page.goto("/signup?role=buyer");
  await page.getByLabel("Your name").fill("Rudo Ncube");
  await page.getByLabel("Phone number").fill("77 412 3089");
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByRole("heading", { name: "Enter your code" })).toBeVisible();
  await page.waitForLoadState("networkidle");
  await page.evaluate(() => document.fonts.ready);
  await expect(page).toHaveScreenshot("02b-sign-in-code.png");
  expect(unexpected, "API calls with no fixture").toEqual([]);
});

test("02c-role-notice", async ({ page }) => {
  // Chose "I need work done", but the number is registered as a worker (issue #9).
  const unexpected = await stubWorld(page, null, { "POST session": { json: WORKER } });
  await page.goto("/signup?role=buyer");
  await page.getByLabel("Your name").fill("Rudo Ncube");
  await page.getByLabel("Phone number").fill("77 412 3089");
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByLabel("6-digit code").fill("123456");
  await expect(page.getByRole("heading", { name: /registered as a worker/ })).toBeVisible();
  await page.waitForLoadState("networkidle");
  await page.evaluate(() => document.fonts.ready);
  await expect(page).toHaveScreenshot("02c-role-notice.png");
  expect(unexpected, "API calls with no fixture").toEqual([]);
});
