import { expect, type Page } from "@playwright/test";

export type Side = "buyer" | "worker";

/**
 * A Zimbabwean mobile number nobody has used yet. The backend's mock
 * `/token` creates an account on first sign-in, so a fresh number is a
 * fresh person and every run starts from an empty account.
 */
export function freshPhone(): string {
  const digits = String(Math.floor(Math.random() * 10_000_000)).padStart(7, "0");
  return `77${digits}`;
}

/**
 * The code a development backend sends to every number (APP_ENV is not
 * "production" in the test stack), so the real code step can be driven.
 */
const DEV_SIGN_IN_CODE = process.env.E2E_SIGN_IN_CODE ?? "123456";

/** Sign up through the real form, the way a person would — code step included. */
export async function signUp(page: Page, side: Side, name: string, phone: string): Promise<void> {
  await page.goto(`/signup?role=${side}`);
  await expect(page.getByRole("heading", { name: "Let's get you set up" })).toBeVisible();
  await page.getByLabel("Your name").fill(name);
  await page.getByLabel("Phone number").fill(phone);
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByRole("heading", { name: "Enter your code" })).toBeVisible();
  await page.getByLabel("6-digit code").fill(DEV_SIGN_IN_CODE);
  await expect(page).toHaveURL(side === "worker" ? /\/worker\/skills$/ : /\/employer$/);
}
