import { describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

const { codeRejectedMessage, isEndpointMissing, readCodeRequestOutcome } =
  await import("@/server/sign-in-code");

describe("readCodeRequestOutcome", () => {
  it.each([404, 405, 501])("treats %i as 'the backend can't send codes yet'", (status) => {
    expect(isEndpointMissing(status)).toBe(true);
    expect(readCodeRequestOutcome(status, null)).toEqual({
      status: 200,
      body: { code_required: false },
    });
  });

  it("asks for the code once one was sent, with the backend's resend wait", () => {
    expect(readCodeRequestOutcome(202, { resend_after_seconds: 45 })).toEqual({
      status: 200,
      body: { code_required: true, resend_after_seconds: 45 },
    });
  });

  it("falls back to a 30 s resend wait and caps silly values", () => {
    expect(readCodeRequestOutcome(202, null).body).toEqual({
      code_required: true,
      resend_after_seconds: 30,
    });
    expect(readCodeRequestOutcome(200, { resend_after_seconds: 99_999 }).body).toEqual({
      code_required: true,
      resend_after_seconds: 600,
    });
  });

  it("passes rate limits through and hides backend failures behind 502", () => {
    expect(readCodeRequestOutcome(429, { detail: "OTP already requested" })).toEqual({
      status: 429,
      body: {
        detail: "We sent you a code a moment ago. Use that one, or ask again in a few minutes.",
      },
    });
    expect(readCodeRequestOutcome(500, { detail: "boom" }).status).toBe(502);
    expect(readCodeRequestOutcome(422, { detail: "Bad phone" })).toEqual({
      status: 422,
      body: { detail: "Bad phone" },
    });
  });
});

describe("codeRejectedMessage", () => {
  it("explains a wrong or expired code", () => {
    expect(codeRejectedMessage(400, null)).toMatch(/isn't right/);
    expect(codeRejectedMessage(401, { detail: "Code expired" })).toBe("Code expired");
    expect(codeRejectedMessage(429, null)).toMatch(/Too many tries/);
    expect(codeRejectedMessage(500, null)).toBe("Sign-in failed. Please try again.");
  });
});
