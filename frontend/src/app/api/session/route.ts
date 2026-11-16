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

const phoneSchema = z.string().regex(/^\+?\d{9,15}$/, "Enter a valid phone number");
const passwordSchema = z.string().min(8, "Use at least 8 characters").max(72);

const signUpSchema = z.object({
  mode: z.literal("signup"),
  phone: phoneSchema,
  password: passwordSchema,
  name: z.string().min(2, "Tell us your name").max(100),
  role: z.enum(["BUYER", "WORKER"]),
});

const signInSchema = z.object({
  mode: z.literal("signin"),
  phone: phoneSchema,
  password: passwordSchema,
});

const loginSchema = z.discriminatedUnion("mode", [signUpSchema, signInSchema]);

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

function detailOf(payload: unknown, fallback: string): string {
  if (typeof payload === "object" && payload !== null && "detail" in payload) {
    const detail = (payload as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
  }
  return fallback;
}

/** Create a new account with a phone number, password and name. */
function signUp(data: z.infer<typeof signUpSchema>): Promise<Response> {
  return backendFetch(BACKEND_ROUTES.authSignUp.path, {
    method: BACKEND_ROUTES.authSignUp.method,
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      phone: data.phone,
      password: data.password,
      name: data.name,
      role: data.role,
    }),
  });
}

/** Sign in with an existing account's phone number and password. */
function signIn(data: z.infer<typeof signInSchema>): Promise<Response> {
  return backendFetch(BACKEND_ROUTES.authSignIn.path, {
    method: BACKEND_ROUTES.authSignIn.method,
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ phone: data.phone, password: data.password }),
  });
}

/**
 * Sign up or sign in with a phone number and password.
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
  const data = parsed.data;

  try {
    const tokenResponse = data.mode === "signup" ? await signUp(data) : await signIn(data);
    if (!tokenResponse.ok) {
      const payload: unknown = await tokenResponse.json().catch(() => null);
      const fallback =
        data.mode === "signup"
          ? "Could not create your account."
          : "Incorrect phone number or password.";
      return NextResponse.json(
        { detail: detailOf(payload, fallback) },
        { status: tokenResponse.status },
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
