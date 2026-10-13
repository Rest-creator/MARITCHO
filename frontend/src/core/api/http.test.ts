import { afterEach, describe, expect, it, vi } from "vitest";
import { z } from "zod";

import { ApiError, apiRequest } from "@/core/api/http";

function respond(status: number, body: unknown): Response {
  return new Response(body === null ? null : JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("apiRequest", () => {
  it("calls the BFF and parses the response with the schema", async () => {
    const fetchMock = vi.fn().mockResolvedValue(respond(200, { value: "7.50" }));
    vi.stubGlobal("fetch", fetchMock);

    const result = await apiRequest("/jobs/open", {
      schema: z.object({ value: z.string().transform(Number) }),
    });

    expect(result).toEqual({ value: 7.5 });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/jobs/open",
      expect.objectContaining({ method: "GET", credentials: "same-origin" }),
    );
  });

  it("sends JSON bodies for writes", async () => {
    const fetchMock = vi.fn().mockResolvedValue(respond(204, null));
    vi.stubGlobal("fetch", fetchMock);

    await apiRequest("/jobs/1/messages/read", { method: "POST", body: { a: 1 } });

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(init.body).toBe('{"a":1}');
    expect(init.headers).toEqual({ "content-type": "application/json" });
  });

  it("surfaces the backend's detail message", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(respond(409, { detail: "Job is no longer open for offers" })),
    );

    await expect(apiRequest("/jobs/1/offers", { method: "POST", body: {} })).rejects.toMatchObject({
      message: "Job is no longer open for offers",
      status: 409,
    });
  });

  it("reads the first FastAPI validation message", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(respond(422, { detail: [{ msg: "Input should be greater than 0" }] })),
    );

    await expect(apiRequest("/x", { method: "POST", body: {} })).rejects.toThrow(
      "Input should be greater than 0",
    );
  });

  it("falls back to a friendly message when there is no detail", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(respond(500, null)));
    await expect(apiRequest("/x")).rejects.toThrow("Maricho is having trouble");
  });

  it("marks a failed connection as a network error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    const error = await apiRequest("/x").catch((caught: unknown) => caught);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).isNetwork).toBe(true);
    expect((error as ApiError).status).toBe(0);
  });

  it("flags 401s so the session can be refreshed", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(respond(401, { detail: "Not authenticated" })),
    );
    const error = (await apiRequest("/x").catch((caught: unknown) => caught)) as ApiError;
    expect(error.isUnauthorized).toBe(true);
  });
});
