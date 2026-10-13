import { describe, expect, it } from "vitest";

import type { Message } from "@/core/api/schemas";
import { groupByDay } from "@/features/messaging/ChatScreen";
import { mergeMessage } from "@/features/messaging/hooks";

function message(id: string, createdAt: string): Message {
  return {
    id,
    job_id: "j",
    sender_id: "s",
    message_type: "TEXT",
    body: id,
    media_url: null,
    duration_seconds: null,
    latitude: null,
    longitude: null,
    created_at: createdAt,
    read_at: null,
  };
}

describe("mergeMessage", () => {
  it("appends in chronological order", () => {
    const merged = mergeMessage(
      [message("b", "2026-10-13T10:05:00Z")],
      message("a", "2026-10-13T10:00:00Z"),
    );
    expect(merged.map((m) => m.id)).toEqual(["a", "b"]);
  });

  it("replaces a message delivered twice (POST response + socket push)", () => {
    const first = message("a", "2026-10-13T10:00:00Z");
    const merged = mergeMessage([first], { ...first, read_at: "2026-10-13T10:01:00Z" });
    expect(merged).toHaveLength(1);
    expect(merged[0]?.read_at).not.toBeNull();
  });

  it("handles an empty cache", () => {
    expect(mergeMessage(undefined, message("a", "2026-10-13T10:00:00Z"))).toHaveLength(1);
  });
});

describe("groupByDay", () => {
  it("groups consecutive messages under day labels", () => {
    const now = new Date("2026-10-13T12:00:00Z");
    const groups = groupByDay(
      [
        message("1", "2026-10-12T09:00:00Z"),
        message("2", "2026-10-13T08:00:00Z"),
        message("3", "2026-10-13T09:00:00Z"),
      ],
      now,
    );
    expect(groups.map((group) => [group.label, group.messages.length])).toEqual([
      ["Yesterday", 1],
      ["Today", 2],
    ]);
  });
});
