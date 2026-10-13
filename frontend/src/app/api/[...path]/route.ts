import { NextResponse, type NextRequest } from "next/server";

import { backendUrl, isProxyPathAllowed, readSessionToken } from "@/server/backend";

type RouteContext = { params: Promise<{ path: string[] }> };

const FORWARDED_REQUEST_HEADERS = ["content-type", "accept", "traceparent", "tracestate"] as const;

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
  const token = readSessionToken(request);
  if (token !== null) {
    headers.set("authorization", `Bearer ${token}`);
  }

  const hasBody = request.method !== "GET" && request.method !== "HEAD";
  const target = `${backendUrl(`/${path.map(encodeURIComponent).join("/")}`)}${request.nextUrl.search}`;

  try {
    const upstream = await fetch(target, {
      method: request.method,
      headers,
      body: hasBody ? await request.arrayBuffer() : undefined,
      cache: "no-store",
    });
    const responseHeaders = new Headers();
    const contentType = upstream.headers.get("content-type");
    if (contentType !== null) {
      responseHeaders.set("content-type", contentType);
    }
    responseHeaders.set("cache-control", "no-store");
    const body = upstream.status === 204 ? null : await upstream.arrayBuffer();
    return new Response(body, { status: upstream.status, headers: responseHeaders });
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
