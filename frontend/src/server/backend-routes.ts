/*
 * Every FastAPI route the BFF depends on, in one place (ADR-009). When the
 * backend renames something, this file changes and neither app does.
 *
 * CI checks each entry against the running backend's /openapi.json
 * (e2e/lifecycle/backend-contract.spec.ts), so a rename fails the build
 * instead of silently switching a feature off in the apps.
 *
 * No `server-only` import here: the drift check reads it from Node.
 */

export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export interface BackendRoute {
  method: HttpMethod;
  /** OpenAPI-style path, e.g. `/media/{media_id}`. */
  path: string;
}

/** Routes the BFF calls itself, translating between the apps and FastAPI. */
export const BACKEND_ROUTES = {
  /** Development-only sign-in without a code; 404 when APP_ENV=production. */
  devToken: { method: "POST", path: "/token" },
  me: { method: "GET", path: "/users/me" },
  /** Send a 6-digit sign-in code (issue #5). */
  otpRequest: { method: "POST", path: "/otp/request" },
  /** Exchange the code (plus role, for new accounts) for a token. */
  otpVerify: { method: "POST", path: "/otp/verify" },
  /** Multipart upload of a photo or voice note (issue #1). */
  mediaUpload: { method: "POST", path: "/media/upload" },
} as const satisfies Record<string, BackendRoute>;

/**
 * Routes the apps reach through the pass-through proxy (`/api/<path>`),
 * web and mobile together. Listed so the drift check covers them too.
 */
export const PROXIED_ROUTES: readonly BackendRoute[] = [
  { method: "GET", path: "/suburbs" },
  { method: "GET", path: "/jobs/mine" },
  { method: "POST", path: "/jobs/request" },
  { method: "GET", path: "/jobs/open" },
  { method: "GET", path: "/jobs/assigned" },
  { method: "GET", path: "/jobs/my-offers" },
  { method: "GET", path: "/jobs/{job_id}" },
  { method: "GET", path: "/jobs/{job_id}/matches" },
  { method: "POST", path: "/jobs/{job_id}/offers" },
  { method: "POST", path: "/jobs/{job_id}/book" },
  { method: "POST", path: "/jobs/{job_id}/quote" },
  { method: "POST", path: "/jobs/{job_id}/complete" },
  { method: "POST", path: "/jobs/{job_id}/dispute" },
  { method: "POST", path: "/jobs/{job_id}/dispute/respond" },
  { method: "GET", path: "/jobs/{job_id}/disputes" },
  { method: "GET", path: "/jobs/{job_id}/record" },
  { method: "GET", path: "/jobs/{job_id}/messages" },
  { method: "POST", path: "/jobs/{job_id}/messages" },
  { method: "POST", path: "/jobs/{job_id}/messages/read" },
  { method: "GET", path: "/workers/me/skills" },
  { method: "POST", path: "/workers/me/skills" },
  { method: "GET", path: "/workers/me/service-areas" },
  { method: "POST", path: "/workers/me/service-areas" },
  { method: "GET", path: "/workers/me/standing" },
  { method: "GET", path: "/workers/me/references" },
  { method: "GET", path: "/media/{media_id}" },
];

/** Fill `{params}` in a route path, URL-encoding each value. */
export function routePath(route: BackendRoute, params: Record<string, string> = {}): string {
  return route.path.replace(/\{(\w+)\}/g, (_match: string, name: string) => {
    const value = params[name];
    if (value === undefined) throw new Error(`Missing path parameter "${name}" for ${route.path}`);
    return encodeURIComponent(value);
  });
}
