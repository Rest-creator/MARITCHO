import "server-only";

import type { NextRequest } from "next/server";

export const SESSION_COOKIE = "maricho_session";

/** Matches ACCESS_TOKEN_EXPIRE_MINUTES in backend/app/core/security.py (7 days). */
export const SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 7;

// 127.0.0.1, not "localhost": Node may resolve localhost to ::1, which Docker
// Desktop's port forwarding does not answer — requests then hang silently.
const DEFAULT_BACKEND_URL = "http://127.0.0.1:8000";

/** Give up on the backend after this long so nobody is left on a spinner. */
export const BACKEND_TIMEOUT_MS = 15_000;

/** fetch() to the backend with a timeout; rejects on network failure or timeout. */
export function backendFetch(path: string, init: RequestInit = {}): Promise<Response> {
  return fetch(backendUrl(path), {
    ...init,
    cache: "no-store",
    signal: AbortSignal.timeout(BACKEND_TIMEOUT_MS),
  });
}

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
  // Photo and voice-note uploads, and reading them back (WEB-004, issue #1).
  "media",
]);

/**
 * Largest upload the proxy passes on. Photos are shrunk on the phone to well
 * under this; anything bigger is refused before it costs anyone data twice.
 */
export const MAX_UPLOAD_BYTES = 4 * 1024 * 1024;

export function isProxyPathAllowed(segments: readonly string[]): boolean {
  const [root] = segments;
  if (root === undefined || !PROXY_ALLOWED_ROOTS.has(root)) {
    return false;
  }
  return segments.every((segment) => segment !== ".." && segment !== "." && segment !== "");
}
