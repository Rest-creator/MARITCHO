import { NextResponse, type NextRequest } from "next/server";
import { z } from "zod";

import { backendFetch } from "@/server/backend";
import { BACKEND_ROUTES } from "@/server/backend-routes";
import { readCodeRequestOutcome } from "@/server/sign-in-code";

const requestSchema = z.object({
  phone: z.string().regex(/^\+?\d{9,15}$/, "Enter a valid phone number"),
});

/**
 * Ask the backend to send a 6-digit sign-in code (BACK-009, issue #5).
 *
 * Until the backend can send codes, it answers 404 and this
 * replies `{ code_required: false }`, so sign-up carries on without the
 * code step instead of claiming a code was sent when it wasn't.
 */
export async function POST(request: NextRequest): Promise<NextResponse> {
  const parsed = requestSchema.safeParse(await request.json().catch(() => null));
  if (!parsed.success) {
    return NextResponse.json(
      { detail: parsed.error.issues[0]?.message ?? "Invalid phone number" },
      { status: 422 },
    );
  }

  try {
    const upstream = await backendFetch(BACKEND_ROUTES.otpRequest.path, {
      method: BACKEND_ROUTES.otpRequest.method,
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ phone: parsed.data.phone }),
    });
    const payload: unknown = await upstream.json().catch(() => null);
    const outcome = readCodeRequestOutcome(upstream.status, payload);
    return NextResponse.json(outcome.body, {
      status: outcome.status,
      headers: { "cache-control": "no-store" },
    });
  } catch {
    return NextResponse.json(
      { detail: "Could not reach Maricho. Check your connection and try again." },
      { status: 503 },
    );
  }
}
