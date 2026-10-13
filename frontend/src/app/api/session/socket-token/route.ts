import { NextResponse, type NextRequest } from "next/server";

import { readSessionToken } from "@/server/backend";

/**
 * Hands the session token to the chat screen for the one place it is
 * needed client-side: the backend's WebSocket (`/jobs/{id}/ws?token=`),
 * which browsers cannot open with an Authorization header and which a
 * Next.js route handler cannot proxy. Same-origin only; never cached.
 */
export function GET(request: NextRequest): NextResponse {
  const token = readSessionToken(request);
  if (token === null) {
    return NextResponse.json({ detail: "Not signed in" }, { status: 401 });
  }
  if (request.headers.get("sec-fetch-site") === "cross-site") {
    return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  }
  return NextResponse.json({ token }, { headers: { "cache-control": "no-store" } });
}
