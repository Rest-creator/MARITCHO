import { NextResponse, type NextRequest } from "next/server";

import { MAX_UPLOAD_BYTES, backendFetch, readAccessToken } from "@/server/backend";
import { BACKEND_ROUTES } from "@/server/backend-routes";

/*
 * Uploads (issue #1, ADR-009). The apps' contract is `POST /api/media` and
 * `GET /api/media` ("can I upload yet?"); the backend's is
 * `POST /media/upload`. Reading a file back (`GET /api/media/{id}`) goes
 * through the ordinary proxy.
 */

const UNREACHABLE = { detail: "Could not reach Maricho. Your photo is still on your phone." };

/**
 * Whether uploads exist yet: 200 when the backend has its upload route,
 * 404 while it doesn't. Asked with OPTIONS, which FastAPI answers 405 for
 * a POST-only route and 404 for a missing one, so nothing is uploaded.
 */
export async function GET(): Promise<NextResponse> {
  try {
    const probe = await backendFetch(BACKEND_ROUTES.mediaUpload.path, { method: "OPTIONS" });
    return probe.status === 404
      ? NextResponse.json({ detail: "Uploads are not available yet" }, { status: 404 })
      : NextResponse.json({ available: true }, { headers: { "cache-control": "no-store" } });
  } catch {
    return NextResponse.json(UNREACHABLE, { status: 503 });
  }
}

/** Pass a multipart upload to the backend with the caller's session. */
export async function POST(request: NextRequest): Promise<NextResponse> {
  if (Number(request.headers.get("content-length") ?? "0") > MAX_UPLOAD_BYTES) {
    return NextResponse.json({ detail: "That file is too big to send." }, { status: 413 });
  }
  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  if (contentType !== null) headers.set("content-type", contentType);
  const key = request.headers.get("idempotency-key");
  if (key !== null) headers.set("idempotency-key", key);
  const token = readAccessToken(request);
  if (token !== null) headers.set("authorization", `Bearer ${token}`);

  try {
    const body = await request.arrayBuffer();
    if (body.byteLength > MAX_UPLOAD_BYTES) {
      return NextResponse.json({ detail: "That file is too big to send." }, { status: 413 });
    }
    const upstream = await backendFetch(BACKEND_ROUTES.mediaUpload.path, {
      method: BACKEND_ROUTES.mediaUpload.method,
      headers,
      body,
    });
    const payload: unknown = await upstream.json().catch(() => null);
    return NextResponse.json(payload, {
      status: upstream.status,
      headers: { "cache-control": "no-store" },
    });
  } catch {
    return NextResponse.json(UNREACHABLE, { status: 503 });
  }
}
