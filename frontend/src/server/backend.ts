import "server-only";

import type { NextRequest } from "next/server";

export const SESSION_COOKIE = "maricho_session";

/** Matches ACCESS_TOKEN_EXPIRE_MINUTES in backend/app/core/security.py (7 days). */
export const SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 7;

const DEFAULT_BACKEND_URL = "http://localhost:8000";

export function backendUrl(path: string): string {
  const base = (process.env.BACKEND_URL ?? DEFAULT_BACKEND_URL).replace(/\/+$/, "");
  return `${base}${path.startsWith("/") ? path : `/${path}`}`;
}

export function readSessionToken(request: NextRequest): string | null {
  return request.cookies.get(SESSION_COOKIE)?.value ?? null;
}

export function sessionCookieOptions(maxAge: number = SESSION_MAX_AGE_SECONDS) {
  return {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax" as const,
    path: "/",
    maxAge,
  };
}

/**
 * Only these top-level backend paths are reachable through the BFF proxy.
 * Ops-only surfaces (`/admin/...`) and provider callbacks (`/webhooks/...`)
 * are deliberately not exposed to the browser.
 */
const PROXY_ALLOWED_ROOTS: ReadonlySet<string> = new Set([
  "jobs",
  "workers",
  "suburbs",
  "users",
  "crews",
  "crew-orders",
]);

export function isProxyPathAllowed(segments: readonly string[]): boolean {
  const [root] = segments;
  if (root === undefined || !PROXY_ALLOWED_ROOTS.has(root)) {
    return false;
  }
  return segments.every((segment) => segment !== ".." && segment !== "." && segment !== "");
}
