import "server-only";

import { NextResponse, type NextRequest } from "next/server";

import { backendFetch, readAccessToken } from "@/server/backend";
import type { BackendRoute } from "@/server/backend-routes";

/*
 * Screen endpoints (ADR-009 phase 2): one request from the phone, the
 * backend calls made here in parallel. On a slow mobile connection each
 * round trip costs more than the bytes, and the mobile app used to make
 * these calls one after another.
 */

type Parts = Record<string, BackendRoute>;

function detailOf(payload: unknown): string | null {
  if (typeof payload === "object" && payload !== null && "detail" in payload) {
    const detail = (payload as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
  }
  return null;
}

/**
 * Fetch every part with the caller's session and answer `{ [name]: body }`.
 * All or nothing: a screen built from half its data would mislead, so the
 * first failure decides the response (401 stays 401 so the app signs out).
 */
export async function screenBundle(request: NextRequest, parts: Parts): Promise<NextResponse> {
  const token = readAccessToken(request);
  if (token === null) {
    return NextResponse.json({ detail: "Not signed in" }, { status: 401 });
  }
  const names = Object.keys(parts);

  let responses: Response[];
  try {
    responses = await Promise.all(
      names.map((name) =>
        backendFetch(parts[name]!.path, {
          method: parts[name]!.method,
          headers: { authorization: `Bearer ${token}` },
        }),
      ),
    );
  } catch {
    return NextResponse.json(
      { detail: "Maricho is unreachable right now. Showing what's saved on your phone." },
      { status: 503 },
    );
  }

  const bodies: unknown[] = await Promise.all(
    responses.map((response) => response.json().catch(() => null)),
  );
  const failed = responses.findIndex((response) => !response.ok);
  if (failed !== -1) {
    const status = responses[failed]!.status;
    return NextResponse.json(
      { detail: detailOf(bodies[failed]) ?? "Could not load this screen." },
      { status: status === 401 || status === 403 || status === 404 ? status : 502 },
    );
  }

  const bundle: Record<string, unknown> = {};
  names.forEach((name, index) => {
    bundle[name] = bodies[index];
  });
  return NextResponse.json(bundle, { headers: { "cache-control": "no-store" } });
}
