import "server-only";

/*
 * Pure helpers for the 6-digit sign-in code (WEB-005), kept apart from the
 * route handlers so they can be tested without a server. The backend
 * contract is the one proposed in issue #5:
 *
 *   POST /auth/otp/request { phone }             -> 202 { resend_after_seconds? }
 *   POST /auth/otp/verify  { phone, code, role } -> 200 TokenOut
 */

/** Wait this long before offering "send a new code" if the backend doesn't say. */
export const DEFAULT_RESEND_AFTER_SECONDS = 30;

/** 404/405/501: the backend has no such endpoint yet (not an error for the person). */
export function isEndpointMissing(status: number): boolean {
  return status === 404 || status === 405 || status === 501;
}

function detailOf(payload: unknown): string | null {
  if (typeof payload === "object" && payload !== null && "detail" in payload) {
    const detail = (payload as { detail: unknown }).detail;
    if (typeof detail === "string" && detail.trim() !== "") return detail;
  }
  return null;
}

function resendAfter(payload: unknown): number {
  if (typeof payload === "object" && payload !== null && "resend_after_seconds" in payload) {
    const value = (payload as { resend_after_seconds: unknown }).resend_after_seconds;
    if (typeof value === "number" && Number.isFinite(value) && value >= 0) {
      return Math.min(Math.round(value), 600);
    }
  }
  return DEFAULT_RESEND_AFTER_SECONDS;
}

export interface CodeRequestOutcome {
  status: number;
  body:
    | { code_required: false }
    | { code_required: true; resend_after_seconds: number }
    | { detail: string };
}

/** Turn the backend's answer to "send a code" into what the sign-up screen needs. */
export function readCodeRequestOutcome(status: number, payload: unknown): CodeRequestOutcome {
  if (isEndpointMissing(status)) {
    return { status: 200, body: { code_required: false } };
  }
  if (status >= 200 && status < 300) {
    return {
      status: 200,
      body: { code_required: true, resend_after_seconds: resendAfter(payload) },
    };
  }
  if (status === 429) {
    return {
      status: 429,
      body: { detail: detailOf(payload) ?? "Too many codes asked for. Wait a few minutes." },
    };
  }
  return {
    status: status >= 500 ? 502 : status,
    body: { detail: detailOf(payload) ?? "Could not send a code. Please try again." },
  };
}

/** What to tell someone whose code was not accepted. */
export function codeRejectedMessage(status: number, payload: unknown): string {
  if (status === 429) return "Too many tries. Ask for a new code in a few minutes.";
  if (status === 400 || status === 401 || status === 422) {
    return detailOf(payload) ?? "That code isn't right, or it has expired. Check the message.";
  }
  return "Sign-in failed. Please try again.";
}
