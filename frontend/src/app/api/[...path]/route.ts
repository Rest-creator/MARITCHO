import { NextResponse, type NextRequest } from "next/server";

import {
  MAX_UPLOAD_BYTES,
  backendFetch,
  isProxyPathAllowed,
  readAccessToken,
} from "@/server/backend";

type RouteContext = { params: Promise<{ path: string[] }> };

const FORWARDED_REQUEST_HEADERS = [
  "content-type",
  "accept",
  "traceparent",
  "tracestate",
  // Lets the backend recognise a replayed upload and return the same file.
  "idempotency-key",
  // Voice notes are streamed: the audio player asks for byte ranges.
  "range",
] as const;

const FORWARDED_RESPONSE_HEADERS = [
  "content-type",
  "content-range",
  "accept-ranges",
  "etag",
] as const;

/** Uploaded media never changes, so the phone may keep it for a week. */
const MEDIA_CACHE_CONTROL = "private, max-age=604800, immutable";

function tooBig(): NextResponse {
  return NextResponse.json({ detail: "That file is too big to send." }, { status: 413 });
}

/**
 * Backend-for-frontend proxy: the browser only ever talks to this origin,
 * and the session JWT (an httpOnly cookie) is attached server-side so page
 * scripts never see it. Also sidesteps CORS, which the FastAPI app does not
 * configure.
 */
async function proxy(request: NextRequest, context: RouteContext): Promise<Response> {
  const { path } = await context.params;
  if (!isProxyPathAllowed(path)) {
    return NextResponse.json({ detail: "Not found" }, { status: 404 });
  }

  const headers = new Headers();
  for (const name of FORWARDED_REQUEST_HEADERS) {
    const value = request.headers.get(name);
    if (value !== null) {
      headers.set(name, value);
    }
  }
  const token = readAccessToken(request);
  if (token !== null) {
    headers.set("authorization", `Bearer ${token}`);
  }

  const hasBody = request.method !== "GET" && request.method !== "HEAD";
  if (hasBody && Number(request.headers.get("content-length") ?? "0") > MAX_UPLOAD_BYTES) {
    return tooBig();
  }
  const target = `/${path.map(encodeURIComponent).join("/")}${request.nextUrl.search}`;

  try {
    const body = hasBody ? await request.arrayBuffer() : undefined;
    // Content-Length can be missing (chunked uploads), so check what arrived too.
    if (body !== undefined && body.byteLength > MAX_UPLOAD_BYTES) {
      return tooBig();
    }
    const upstream = await backendFetch(target, { method: request.method, headers, body });
    const responseHeaders = new Headers();
    for (const name of FORWARDED_RESPONSE_HEADERS) {
      const value = upstream.headers.get(name);
      if (value !== null) {
        responseHeaders.set(name, value);
      }
    }
    const isMediaFile = path[0] === "media" && path.length > 1 && request.method === "GET";
    responseHeaders.set(
      "cache-control",
      isMediaFile && upstream.ok ? MEDIA_CACHE_CONTROL : "no-store",
    );
    const responseBody = upstream.status === 204 ? null : await upstream.arrayBuffer();
    return new Response(responseBody, { status: upstream.status, headers: responseHeaders });
  } catch {
    return NextResponse.json(
      { detail: "Maricho is unreachable right now. Your changes are saved and will send later." },
      { status: 503 },
    );
  }
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
