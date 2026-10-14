import { z } from "zod";

import { ApiError } from "@/core/api/http";

const outcomeSchema = z.union([
  z.object({ code_required: z.literal(false) }),
  z.object({ code_required: z.literal(true), resend_after_seconds: z.number().int().min(0) }),
]);

export type CodeRequest =
  { isCodeRequired: false } | { isCodeRequired: true; resendAfterSeconds: number };

/**
 * Ask for a 6-digit sign-in code to be sent to `phone`. Resolves to
 * `isCodeRequired: false` while the backend can't send codes yet, in which
 * case sign-in goes ahead without one.
 */
export async function requestSignInCode(phone: string): Promise<CodeRequest> {
  const response = await fetch("/api/session/code", {
    method: "POST",
    credentials: "same-origin",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ phone }),
  }).catch(() => {
    throw new ApiError("You're offline. Connect to sign in.", 0);
  });
  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const detail =
      typeof payload === "object" && payload !== null && "detail" in payload
        ? String((payload as { detail: unknown }).detail)
        : "Could not send a code. Please try again.";
    throw new ApiError(detail, response.status);
  }
  const outcome = outcomeSchema.parse(payload);
  return outcome.code_required
    ? { isCodeRequired: true, resendAfterSeconds: outcome.resend_after_seconds }
    : { isCodeRequired: false };
}

/** Keep digits only, at most 6 — pasted codes often carry spaces or a dash. */
export function normaliseCode(input: string): string {
  return input.replace(/\D/g, "").slice(0, 6);
}

export function formatCountdown(seconds: number): string {
  const safe = Math.max(0, Math.ceil(seconds));
  return `${Math.floor(safe / 60)}:${String(safe % 60).padStart(2, "0")}`;
}
