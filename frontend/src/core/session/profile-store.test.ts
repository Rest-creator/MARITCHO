import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import {
  EMPTY_PROFILE,
  resetProfileCache,
  updateProfile,
  useLocalProfile,
} from "@/core/session/profile-store";

beforeEach(() => {
  window.localStorage.clear();
  resetProfileCache();
});

describe("local profile", () => {
  it("starts with sensible defaults", () => {
    const { result } = renderHook(() => useLocalProfile());
    expect(result.current).toEqual(EMPTY_PROFILE);
    expect(result.current.travelKm).toBe(10);
    expect(result.current.isAvailable).toBe(true);
  });

  it("persists updates and notifies subscribers", () => {
    const { result } = renderHook(() => useLocalProfile());
    act(() => updateProfile({ name: "Rudo Kanengoni", travelKm: 15 }));
    expect(result.current.name).toBe("Rudo Kanengoni");
    expect(JSON.parse(window.localStorage.getItem("maricho-profile") ?? "{}")).toMatchObject({
      name: "Rudo Kanengoni",
      travelKm: 15,
    });
  });

  it("ignores corrupt storage", () => {
    window.localStorage.setItem("maricho-profile", "{not json");
    const { result } = renderHook(() => useLocalProfile());
    expect(result.current).toEqual(EMPTY_PROFILE);
  });

  it("rejects out-of-range values", () => {
    expect(() => updateProfile({ travelKm: 500 })).toThrow();
  });
});
