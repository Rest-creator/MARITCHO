import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

const { backendFetch, backendUrl, isProxyPathAllowed, sessionCookieOptions } =
  await import("@/server/backend");

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("isProxyPathAllowed", () => {
  it.each([
    [["jobs", "open"], true],
    [["workers", "me", "skills"], true],
    [["suburbs"], true],
    [["users", "me"], true],
    [["admin", "payment-gateways", "ecocash"], false],
    [["webhooks", "ecocash"], false],
    [["token"], false],
    [["jobs", "..", "admin"], false],
    [["jobs", ""], false],
    [[], false],
  ])("%j → %s", (segments, allowed) => {
    expect(isProxyPathAllowed(segments)).toBe(allowed);
  });
});

describe("backendUrl", () => {
  it("joins the configured base without double slashes", () => {
    vi.stubEnv("BACKEND_URL", "http://api:8000/");
    expect(backendUrl("/jobs/open")).toBe("http://api:8000/jobs/open");
    expect(backendUrl("token")).toBe("http://api:8000/token");
  });

  it("defaults to 127.0.0.1 (not localhost, which may resolve to ::1)", () => {
    vi.stubEnv("BACKEND_URL", "");
    delete process.env.BACKEND_URL;
    expect(backendUrl("/x")).toBe("http://127.0.0.1:8000/x");
  });
});

describe("sessionCookieOptions", () => {
  it("is httpOnly and lax, secure only in production", () => {
    vi.stubEnv("NODE_ENV", "production");
    expect(sessionCookieOptions()).toMatchObject({
      httpOnly: true,
      sameSite: "lax",
      secure: true,
      path: "/",
    });
    vi.stubEnv("NODE_ENV", "development");
    expect(sessionCookieOptions(0)).toMatchObject({ secure: false, maxAge: 0 });
  });
});

describe("backendFetch", () => {
  it("always sends a timeout signal and skips the fetch cache", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);
    vi.stubEnv("BACKEND_URL", "http://api:8000");

    await backendFetch("/users/me", { headers: { authorization: "Bearer t" } });

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("http://api:8000/users/me");
    expect(init.signal).toBeInstanceOf(AbortSignal);
    expect(init.cache).toBe("no-store");
    expect(init.headers).toEqual({ authorization: "Bearer t" });
  });
});
