import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

const { screenBundle } = await import("@/server/screen-bundle");

const PARTS = {
  standing: { method: "GET", path: "/workers/me/standing" },
  offers: { method: "GET", path: "/jobs/my-offers" },
} as const;

function request(headers: Record<string, string> = {}): NextRequest {
  return new NextRequest("http://bff.test/api/screens/worker-work", { headers });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("screenBundle", () => {
  it("fetches every part in parallel with the caller's token", async () => {
    const fetchMock = vi.fn(async (url: string) =>
      Response.json(url.endsWith("/standing") ? { grade: "EXPERT" } : [{ id: "o1" }]),
    );
    vi.stubGlobal("fetch", fetchMock);

    const response = await screenBundle(request({ authorization: "Bearer jwt-1" }), PARTS);

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({
      standing: { grade: "EXPERT" },
      offers: [{ id: "o1" }],
    });
    expect(fetchMock).toHaveBeenCalledTimes(2);
    for (const call of fetchMock.mock.calls as unknown as [string, RequestInit][]) {
      expect(new Headers(call[1].headers).get("authorization")).toBe("Bearer jwt-1");
    }
  });

  it("refuses without a session, before calling the backend", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const response = await screenBundle(request(), PARTS);
    expect(response.status).toBe(401);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("is all or nothing: one failing part fails the screen", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) =>
        url.endsWith("/standing")
          ? Response.json({ detail: "Database is down" }, { status: 500 })
          : Response.json([]),
      ),
    );
    const response = await screenBundle(request({ authorization: "Bearer jwt-1" }), PARTS);
    expect(response.status).toBe(502);
    expect(await response.json()).toEqual({ detail: "Database is down" });
  });

  it("keeps an expired session a 401, so the app signs out", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => Response.json({ detail: "Expired" }, { status: 401 })),
    );
    const response = await screenBundle(request({ authorization: "Bearer old" }), PARTS);
    expect(response.status).toBe(401);
  });

  it("says the backend is unreachable when it is", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("fetch failed")));
    const response = await screenBundle(request({ authorization: "Bearer jwt-1" }), PARTS);
    expect(response.status).toBe(503);
  });
});
