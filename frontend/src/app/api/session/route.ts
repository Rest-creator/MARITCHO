import { NextResponse, type NextRequest } from "next/server";
import { z } from "zod";

import { tokenSchema, userSchema } from "@/core/api/schemas";
import {
  SESSION_COOKIE,
  backendFetch,
  isMobileClient,
  readAccessToken,
  sessionCookieOptions,
} from "@/server/backend";
import { BACKEND_ROUTES } from "@/server/backend-routes";
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
  return backendFetch(BACKEND_ROUTES.me.path, {
    headers: { authorization: `Bearer ${token}` },
  });
}

/**
 * Who is signed in — `null` when nobody is (not an error for an anonymous
 * visit). Works for the web cookie and the mobile bearer token alike.
 */
export async function GET(request: NextRequest): Promise<NextResponse> {
  const token = readAccessToken(request);
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
  return backendFetch(BACKEND_ROUTES.otpVerify.path, {
    method: BACKEND_ROUTES.otpVerify.method,
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ phone, code, role }),
  });
}

/** The backend's development-only sign-in (ADR-006): trusts the phone number. */
function mockToken(phone: string, role: string): Promise<Response> {
  return backendFetch(BACKEND_ROUTES.devToken.path, {
    method: BACKEND_ROUTES.devToken.method,
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username: phone, password: "", role }),
  });
}

/**
 * Sign in — with the 6-digit code when the backend sent one, otherwise
 * through the development-only `/token` (BACK-009). `role` only applies on
 * first sign-in.
 *
 * The web app gets an httpOnly cookie and the user. The mobile app
 * (`X-Maricho-Client: mobile`, ADR-009) gets `{ user, access_token }` to
 * keep in its own secure storage and send back as a bearer token.
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
    const user = userSchema.parse(await me.json());
    if (isMobileClient(request)) {
      return NextResponse.json(
        { user, access_token: token },
        { headers: { "cache-control": "no-store" } },
      );
    }
    const response = NextResponse.json(user);
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
