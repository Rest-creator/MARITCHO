import { describe, expect, it } from "vitest";

import { ApiError } from "@/core/api/http";
import { mutationKeys } from "@/core/query/keys";
import { createQueryClient, shouldRetry } from "@/core/query/query-client";
import { pendingLabel } from "@/core/offline/OfflineBanner";

describe("shouldRetry", () => {
  it("retries network and server failures twice", () => {
    expect(shouldRetry(0, new ApiError("offline", 0))).toBe(true);
    expect(shouldRetry(1, new ApiError("down", 503))).toBe(true);
    expect(shouldRetry(2, new ApiError("down", 500))).toBe(false);
  });

  it("never retries a client error", () => {
    expect(shouldRetry(0, new ApiError("nope", 409))).toBe(false);
    expect(shouldRetry(0, new ApiError("auth", 401))).toBe(false);
  });
});

describe("createQueryClient", () => {
  it("registers a replayable default for every offline-capable write", () => {
    const client = createQueryClient();
    for (const key of Object.values(mutationKeys)) {
      expect(client.getMutationDefaults(key).mutationFn).toBeTypeOf("function");
    }
  });

  it("serves cached reads first while offline", () => {
    const client = createQueryClient();
    expect(client.getDefaultOptions().queries?.networkMode).toBe("offlineFirst");
  });
});

describe("pendingLabel", () => {
  it("tells people their changes are safe", () => {
    expect(pendingLabel(0)).toContain("showing what was saved");
    expect(pendingLabel(1)).toContain("1 change saved");
    expect(pendingLabel(3)).toContain("3 changes saved");
  });
});
