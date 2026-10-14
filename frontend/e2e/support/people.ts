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

/** Sign up through the real form, the way a person would. */
export async function signUp(page: Page, side: Side, name: string, phone: string): Promise<void> {
  await page.goto(`/signup?role=${side}`);
  await expect(page.getByRole("heading", { name: "Let's get you set up" })).toBeVisible();
  await page.getByLabel("Your name").fill(name);
  await page.getByLabel("Phone number").fill(phone);
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL(side === "worker" ? /\/worker\/skills$/ : /\/employer$/);
}
