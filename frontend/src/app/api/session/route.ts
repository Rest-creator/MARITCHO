import { NextResponse, type NextRequest } from "next/server";
import { z } from "zod";

import { tokenSchema, userSchema } from "@/core/api/schemas";
import {
  SESSION_COOKIE,
  backendUrl,
  readSessionToken,
  sessionCookieOptions,
} from "@/server/backend";

const loginSchema = z.object({
  phone: z.string().regex(/^\+?\d{9,15}$/, "Enter a valid phone number"),
  role: z.enum(["BUYER", "WORKER"]),
});

function unreachable(): NextResponse {
  return NextResponse.json(
    { detail: "Could not reach Maricho. Check your connection and try again." },
    { status: 503 },
  );
}

async function fetchMe(token: string): Promise<Response> {
  return fetch(backendUrl("/users/me"), {
    headers: { authorization: `Bearer ${token}` },
    cache: "no-store",
  });
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

/**
 * Sign in. The backend's `/token` is a development mock (ADR-006, BACK-009):
 * it trusts the phone number and only applies `role` on first sign-in.
 */
export async function POST(request: NextRequest): Promise<NextResponse> {
  const parsed = loginSchema.safeParse(await request.json().catch(() => null));
  if (!parsed.success) {
    return NextResponse.json(
      { detail: parsed.error.issues[0]?.message ?? "Invalid sign-in details" },
      { status: 422 },
    );
  }

  try {
    const form = new URLSearchParams({
      username: parsed.data.phone,
      password: "",
      role: parsed.data.role,
    });
    const tokenResponse = await fetch(backendUrl("/token"), {
      method: "POST",
      headers: { "content-type": "application/x-www-form-urlencoded" },
      body: form,
      cache: "no-store",
    });
    if (!tokenResponse.ok) {
      return NextResponse.json({ detail: "Sign-in failed" }, { status: tokenResponse.status });
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
