import { NextResponse, type NextRequest } from "next/server";
import { z } from "zod";

import { tokenSchema, userSchema } from "@/core/api/schemas";
import {
  SESSION_COOKIE,
  backendFetch,
  readSessionToken,
  sessionCookieOptions,
} from "@/server/backend";
import { codeRejectedMessage } from "@/server/sign-in-code";

const loginSchema = z.object({
  phone: z.string().regex(/^\+?\d{9,15}$/, "Enter a valid phone number"),
  role: z.enum(["BUYER", "WORKER"]),
  /** The 6-digit code, once the backend sends one (WEB-005). */
  code: z
    .string()
    .regex(/^\d{6}$/, "The code is 6 digits")
    .optional(),
});

function unreachable(): NextResponse {
  return NextResponse.json(
    { detail: "Could not reach Maricho. Check your connection and try again." },
    { status: 503 },
  );
}

async function fetchMe(token: string): Promise<Response> {
  return backendFetch("/users/me", { headers: { authorization: `Bearer ${token}` } });
}

/** Who is signed in — `null` when nobody is (not an error for an anonymous visit). */
export async function GET(request: NextRequest): Promise<NextResponse> {
  const token = readSessionToken(request);
  if (token === null) {
    return NextResponse.json(null);
  }
  try {
    const me = await fetchMe(token);
    if (!me.ok) {
      const response = NextResponse.json({ detail: "Session expired" }, { status: 401 });
      response.cookies.set(SESSION_COOKIE, "", sessionCookieOptions(0));
      return response;
    }
    return NextResponse.json(userSchema.parse(await me.json()));
  } catch {
    return unreachable();
  }
}

/** Exchange a 6-digit code for a token (issue #5); `role` applies to new accounts only. */
function verifyCode(phone: string, code: string, role: string): Promise<Response> {
  return backendFetch("/auth/otp/verify", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ phone, code, role }),
  });
}

/** The backend's `/token` development mock (ADR-006): trusts the phone number. */
function mockToken(phone: string, role: string): Promise<Response> {
  return backendFetch("/token", {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username: phone, password: "", role }),
  });
}

/**
 * Sign in — with the 6-digit code when the backend sent one, otherwise
 * through the `/token` mock (BACK-009). `role` only applies on first sign-in.
 */
export async function POST(request: NextRequest): Promise<NextResponse> {
  const parsed = loginSchema.safeParse(await request.json().catch(() => null));
  if (!parsed.success) {
    return NextResponse.json(
      { detail: parsed.error.issues[0]?.message ?? "Invalid sign-in details" },
      { status: 422 },
    );
  }
  const { phone, role, code } = parsed.data;

  try {
    const tokenResponse =
      code === undefined ? await mockToken(phone, role) : await verifyCode(phone, code, role);
    if (!tokenResponse.ok) {
      const payload: unknown = await tokenResponse.json().catch(() => null);
      return code === undefined
        ? NextResponse.json({ detail: "Sign-in failed" }, { status: tokenResponse.status })
        : NextResponse.json(
            { detail: codeRejectedMessage(tokenResponse.status, payload) },
            // Never 401: that would read as "your session expired" to the app.
            { status: tokenResponse.status === 429 ? 429 : 400 },
          );
    }
    const { access_token: token } = tokenSchema.parse(await tokenResponse.json());

    const me = await fetchMe(token);
    if (!me.ok) {
      return NextResponse.json({ detail: "Sign-in failed" }, { status: me.status });
    }
    const response = NextResponse.json(userSchema.parse(await me.json()));
    response.cookies.set(SESSION_COOKIE, token, sessionCookieOptions());
    return response;
  } catch {
    return unreachable();
  }
}

/** Sign out. */
export async function DELETE(): Promise<NextResponse> {
  const response = new NextResponse(null, { status: 204 });
  response.cookies.set(SESSION_COOKIE, "", sessionCookieOptions(0));
  return response;
}
