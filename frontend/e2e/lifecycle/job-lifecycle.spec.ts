import { expect, test, type Page } from "@playwright/test";

import { freshPhone, signUp } from "../support/people";

/*
 * One job from start to finish, through the UI only, against the real
 * backend: a worker sets up, a buyer posts, the worker offers, the buyer
 * hires, both chat live, the worker prices it on site, the buyer signs it
 * off, and the worker sees the money.
 *
 * Other runs leave their jobs and workers in the same database, so
 * everything this run creates carries `runId` and is found by it.
 */

const SUBURB = "Hillside";
const PRICE = 40;

/** Reload until `check` passes: for screens that only refetch on load. */
async function untilAfterReload(page: Page, check: () => Promise<void>): Promise<void> {
  await expect(async () => {
    await page.reload();
    await check();
  }).toPass({ timeout: 30_000, intervals: [1_000, 2_000, 3_000] });
}

test("a job goes from posted to paid", async ({ browser }) => {
  const runId = Math.random().toString(36).slice(2, 8);
  const jobText = `Kitchen sink leaking ${runId}`;
  const offerNote = `I can come at 2pm ${runId}`;

  const buyerContext = await browser.newContext();
  const workerContext = await browser.newContext();
  const buyer = await buyerContext.newPage();
  const worker = await workerContext.newPage();

  await test.step("worker signs up and picks skills", async () => {
    await signUp(worker, "worker", "Tendai Moyo", freshPhone());
    await expect(worker.getByRole("heading", { name: "What work can you do?" })).toBeVisible();
    await worker.getByRole("button", { name: "Plumber" }).click();
    await worker.getByLabel("From").selectOption(SUBURB);
    await worker.getByRole("button", { name: "Start finding work" }).click();
    await expect(worker).toHaveURL(/\/worker$/);
    await expect(worker.getByRole("heading", { name: "Jobs near you" })).toBeVisible();
  });

  let jobUrl = "";
  await test.step("buyer signs up and posts a job", async () => {
    await signUp(buyer, "buyer", "Rudo Ncube", freshPhone());
    await buyer.goto("/employer/post?trade=PLUMBING");
    await buyer.getByLabel("Describe the job").fill(jobText);
    await buyer.getByRole("button", { name: /Where is the job\?/ }).click();
    const sheet = buyer.getByRole("dialog", { name: "Where is the job?" });
    await sheet.getByLabel("Suburb").selectOption(SUBURB);
    await sheet.getByLabel("Street address").fill("14 Harrow Rd");
    await sheet.getByRole("button", { name: "Use this place" }).click();
    await buyer.getByLabel("Your budget (optional)").fill(String(PRICE));
    await buyer.getByRole("button", { name: "Find someone for this job" }).click();
    await expect(buyer).toHaveURL(/\/employer\/jobs\/[^/]+$/);
    await expect(buyer.getByRole("heading", { name: jobText })).toBeVisible();
    jobUrl = buyer.url();
  });

  await test.step("worker finds the job and sends an offer", async () => {
    const card = worker.getByRole("article").filter({ hasText: jobText });
    await untilAfterReload(worker, () => expect(card).toBeVisible({ timeout: 2_000 }));
    await card.getByRole("link", { name: "I can do this" }).click();
    await expect(worker.getByRole("heading", { name: jobText })).toBeVisible();
    await expect(worker.getByLabel("Your price in US dollars")).toHaveValue(String(PRICE));
    await worker.getByLabel("When you can come").fill(offerNote);
    await worker.getByRole("button", { name: "Send my offer" }).click();
    await expect(worker).toHaveURL(/\/worker\/work\?tab=offers$/);
    await expect(worker.getByRole("tab", { name: "Offers (1)" })).toBeVisible();
  });

  await test.step("buyer sees the offer and hires", async () => {
    const candidate = buyer.getByRole("article").filter({ hasText: offerNote });
    await untilAfterReload(buyer, () => expect(candidate).toBeVisible({ timeout: 2_000 }));
    await expect(candidate).toContainText(`$${PRICE}`);
    await candidate.getByRole("button", { name: "Hire" }).click();
    await buyer.getByRole("button", { name: /^Hire · hold \$\d+ deposit$/ }).click();
    await expect(buyer).toHaveURL(`${jobUrl}/track`);
    await expect(buyer.getByText("Your worker is on the way")).toBeVisible();
  });

  await test.step("worker arrives and confirms the price", async () => {
    await worker.goto("/worker/work?tab=active");
    const job = worker.getByRole("article").filter({ hasText: jobText });
    await expect(job).toContainText("You got the job");
    await expect(job).toContainText(`14 Harrow Rd, ${SUBURB}`);
    await job.getByRole("button", { name: "I've arrived" }).click();
    const sheet = worker.getByRole("dialog", { name: "Confirm the price" });
    await expect(sheet.getByLabel("Your work")).toHaveValue(String(PRICE));
    await sheet.getByRole("button", { name: `Send price · $${PRICE}` }).click();
    await expect(sheet).toBeHidden();
    await expect(job).toContainText("Price agreed · working");
  });

  await test.step("both sides chat live", async () => {
    await buyer.goto(`${jobUrl}/track`);
    await expect(buyer.getByText(`Price confirmed: $${PRICE}`)).toBeVisible();
    await buyer.getByRole("link", { name: "Message" }).click();
    await expect(buyer).toHaveURL(/\/chat\/[^/]+$/);
    const chatUrl = buyer.url();
    await worker.goto(chatUrl);

    const live = "Connected · messages arrive instantly";
    await expect(buyer.getByText(live)).toBeVisible();
    await expect(worker.getByText(live)).toBeVisible();

    const hello = `Gate code is 1234 (${runId})`;
    await buyer.getByLabel("Message").fill(hello);
    await buyer.getByRole("button", { name: "Send" }).click();
    // No reload: it has to arrive over the WebSocket.
    await expect(worker.getByText(hello)).toBeVisible();

    const reply = `Thanks, see you soon (${runId})`;
    await worker.getByLabel("Message").fill(reply);
    await worker.getByRole("button", { name: "Send" }).click();
    await expect(buyer.getByText(reply)).toBeVisible();
  });

  await test.step("buyer reviews and signs the job off", async () => {
    await buyer.goto(`${jobUrl}/track`);
    await expect(buyer.getByRole("heading", { name: "How did they do?" })).toBeVisible();
    await buyer.getByRole("radio", { name: "4 stars" }).click();
    await buyer.getByRole("button", { name: "On time" }).click();
    await buyer.getByRole("button", { name: `Confirm job done & pay $${PRICE}` }).click();
    await expect(buyer.getByText("Job signed off")).toBeVisible();
    await expect(buyer.getByText("Confirmed through Maricho")).toBeVisible();
  });

  await test.step("worker sees the finished job and the earnings", async () => {
    await worker.goto("/worker/work?tab=done");
    await expect(worker.getByText(jobText)).toBeVisible();
    const month = worker.getByRole("region", { name: "This month" });
    await expect(month).toContainText(`$${PRICE}`);
  });

  await buyerContext.close();
  await workerContext.close();
});
