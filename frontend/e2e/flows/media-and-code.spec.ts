import { expect, test, type Page } from "@playwright/test";

import { BUYER, LIVE_JOB_ID, NOW, OPEN_JOB, stubWorld, type Reply } from "../visual/fixtures";

/*
 * WEB-004 and WEB-005 in a real browser, with the backend endpoints that
 * don't exist yet (issues #1 and #5) stubbed to their proposed contract.
 * Photo shrinking needs a real canvas, which unit tests don't have.
 */

const STORED: Reply = {
  status: 201,
  json: { url: "/media/new.jpg", content_type: "image/jpeg", size_bytes: 1 },
};

/** A camera-sized (4000×3000) JPEG, drawn in the page. */
async function bigPhoto(page: Page): Promise<Buffer> {
  const base64 = await page.evaluate(() => {
    const canvas = document.createElement("canvas");
    canvas.width = 4000;
    canvas.height = 3000;
    const context = canvas.getContext("2d");
    if (context === null) throw new Error("no canvas");
    const gradient = context.createLinearGradient(0, 0, 4000, 3000);
    gradient.addColorStop(0, "#1e3a8a");
    gradient.addColorStop(1, "#f59e0b");
    context.fillStyle = gradient;
    context.fillRect(0, 0, 4000, 3000);
    return canvas.toDataURL("image/jpeg", 0.95).split(",")[1] ?? "";
  });
  return Buffer.from(base64, "base64");
}

/** Width × height from a JPEG's SOF marker. */
function jpegSize(bytes: Buffer): { width: number; height: number } {
  for (let offset = 2; offset < bytes.length - 9; offset += 1) {
    const marker = bytes[offset + 1] ?? 0;
    if (bytes[offset] === 0xff && marker >= 0xc0 && marker <= 0xc2) {
      return { height: bytes.readUInt16BE(offset + 5), width: bytes.readUInt16BE(offset + 7) };
    }
  }
  throw new Error("Not a JPEG");
}

/** The file part of a multipart upload. */
function uploadedFile(body: Buffer): Buffer {
  const start = body.indexOf(Buffer.from([0xff, 0xd8]));
  const end = body.lastIndexOf(Buffer.from([0xff, 0xd9]));
  return body.subarray(start, end + 2);
}

test.describe("sign-in code (WEB-005)", () => {
  test("asks for the code that was sent and signs in with it", async ({ page }) => {
    const unexpected = await stubWorld(page, null, { "POST session": { json: BUYER } });
    await page.goto("/signup?role=buyer");
    await page.getByLabel("Your name").fill("Rudo Ncube");
    await page.getByLabel("Phone number").fill("77 412 3089");
    await page.getByRole("button", { name: "Continue" }).click();

    await expect(page.getByText("+263 77 412 3089")).toBeVisible();
    const signIn = page.waitForRequest((request) => request.url().endsWith("/api/session"));
    await page.getByLabel("6-digit code").fill("482913");
    expect((await signIn).postDataJSON()).toEqual({
      phone: "+263774123089",
      role: "BUYER",
      code: "482913",
    });
    await expect(page).toHaveURL(/\/employer$/);
    expect(unexpected).toEqual([]);
  });

  test("goes straight in while the backend can't send codes", async ({ page }) => {
    const unexpected = await stubWorld(page, null, {
      "POST session/code": { json: { code_required: false } },
      "POST session": { json: BUYER },
    });
    await page.goto("/signup?role=buyer");
    await page.getByLabel("Your name").fill("Rudo Ncube");
    await page.getByLabel("Phone number").fill("77 412 3089");
    const signIn = page.waitForRequest((request) => request.url().endsWith("/api/session"));
    await page.getByRole("button", { name: "Continue" }).click();

    expect((await signIn).postDataJSON()).toEqual({ phone: "+263774123089", role: "BUYER" });
    await expect(page).toHaveURL(/\/employer$/);
    await expect(page.getByRole("heading", { name: "Enter your code" })).toHaveCount(0);
    expect(unexpected).toEqual([]);
  });
});

test.describe("photos (WEB-004)", () => {
  test("a job photo is shrunk on the phone, uploaded, and attached", async ({ page }) => {
    const unexpected = await stubWorld(page, "BUYER", {
      "POST media": STORED,
      "POST jobs/request": { status: 201, json: OPEN_JOB },
    });
    await page.goto("/employer/post?trade=PLUMBING");
    await page.getByLabel("Describe the job").fill("Kitchen sink is leaking under the basin");
    await page.getByRole("button", { name: /Where is the job\?/ }).click();
    const sheet = page.getByRole("dialog", { name: "Where is the job?" });
    await sheet.getByLabel("Suburb").selectOption("Hillside");
    await sheet.getByLabel("Street address").fill("14 Harrow Rd");
    await sheet.getByRole("button", { name: "Use this place" }).click();

    const photo = await bigPhoto(page);
    await page
      .getByTestId("photo-gallery-input")
      .setInputFiles({ name: "IMG_2041.jpg", mimeType: "image/jpeg", buffer: photo });
    await expect(page.getByRole("button", { name: "Remove photo" })).toBeVisible();

    const upload = page.waitForRequest((request) => request.url().endsWith("/api/media"));
    const post = page.waitForRequest((request) => request.url().endsWith("/api/jobs/request"));
    await page.getByRole("button", { name: "Find someone for this job" }).click();

    const uploadRequest = await upload;
    expect(uploadRequest.headers()["idempotency-key"]).toMatch(/.{8,}/);
    const sent = uploadedFile(uploadRequest.postDataBuffer() ?? Buffer.alloc(0));
    expect(jpegSize(sent)).toEqual({ width: 1280, height: 960 });
    expect(sent.length).toBeLessThan(photo.length / 3);
    expect((await post).postDataJSON()).toMatchObject({ problem_photo_url: "/media/new.jpg" });
    await expect(page).toHaveURL(/\/employer\/jobs\/job-open$/);
    expect(unexpected).toEqual([]);
  });

  test("a photo sent in chat goes up first, then as a PHOTO message", async ({ page }) => {
    const unexpected = await stubWorld(page, "BUYER", {
      "POST media": STORED,
      [`POST jobs/${LIVE_JOB_ID}/messages`]: {
        status: 201,
        json: {
          id: "m-photo",
          job_id: LIVE_JOB_ID,
          sender_id: BUYER.id,
          message_type: "PHOTO",
          body: null,
          media_url: "/media/new.jpg",
          duration_seconds: null,
          latitude: null,
          longitude: null,
          created_at: NOW.toISOString(),
          read_at: null,
        },
      },
    });
    await page.goto(`/chat/${LIVE_JOB_ID}`);
    await expect(page.getByText("Okay, go ahead.")).toBeVisible();
    await expect(page.getByRole("button", { name: "Send a photo" })).toBeVisible();

    const message = page.waitForRequest(
      (request) =>
        request.url().endsWith(`/api/jobs/${LIVE_JOB_ID}/messages`) && request.method() === "POST",
    );
    await page
      .locator(".chat__composer")
      .getByTestId("photo-gallery-input")
      .setInputFiles({ name: "wire.jpg", mimeType: "image/jpeg", buffer: await bigPhoto(page) });

    expect((await message).postDataJSON()).toEqual({
      message_type: "PHOTO",
      media_url: "/media/new.jpg",
    });
    await expect(page.getByRole("button", { name: /Photo · tap to load/ })).toBeVisible();
    expect(unexpected).toEqual([]);
  });
});
