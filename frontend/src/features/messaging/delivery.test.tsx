import { QueryClient } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { TabBar } from "@/components/ui/TabBar";
import { messageSchema, normalizeIsoDate } from "@/core/api/schemas";
import { queryKeys } from "@/core/query/keys";
import { applySocketPayload, unreadTotal } from "@/features/messaging/hooks";

vi.mock("next/navigation", () => ({ usePathname: () => "/worker" }));

const JOB_ID = "6b1d2a52-6d0e-4b8f-9d3f-1f3c2c2b9a10";
const MESSAGE = {
  id: "0e1b0c4e-5b6a-4f3d-8e2a-7c9d1b2a3f40",
  job_id: JOB_ID,
  sender_id: "9a8b7c6d-5e4f-4a3b-9c2d-1e0f9a8b7c6d",
  message_type: "TEXT",
  body: "On my way",
  media_url: null,
  duration_seconds: null,
  latitude: null,
  longitude: null,
  created_at: "2026-11-17T10:00:00",
  read_at: null,
};

describe("message timestamps", () => {
  it("reads a UTC time without an offset as UTC, not local time", () => {
    expect(normalizeIsoDate("2026-11-17T10:00:00")).toBe("2026-11-17T10:00:00Z");
    expect(normalizeIsoDate("2026-11-17T10:00:00.123456")).toBe("2026-11-17T10:00:00.123456Z");
    expect(new Date(normalizeIsoDate("2026-11-17T10:00:00")).toISOString()).toBe(
      "2026-11-17T10:00:00.000Z",
    );
  });

  it("leaves times that already carry an offset, and plain dates, alone", () => {
    expect(normalizeIsoDate("2026-11-17T10:00:00Z")).toBe("2026-11-17T10:00:00Z");
    expect(normalizeIsoDate("2026-11-17T12:00:00+02:00")).toBe("2026-11-17T12:00:00+02:00");
    expect(normalizeIsoDate("2026-11-17")).toBe("2026-11-17");
  });

  it("applies when parsing messages from the API or the socket", () => {
    expect(messageSchema.parse(MESSAGE).created_at).toBe("2026-11-17T10:00:00Z");
  });
});

describe("live chat socket frames", () => {
  it("treats heartbeats as keep-alive only (no refetch)", () => {
    const client = new QueryClient();
    const invalidate = vi.spyOn(client, "invalidateQueries");

    expect(applySocketPayload(client, JOB_ID, '{"type":"ping"}')).toBe(false);
    expect(invalidate).not.toHaveBeenCalled();
  });

  it("adds a pushed message to the thread and refreshes unread counts", () => {
    const client = new QueryClient();
    const invalidate = vi.spyOn(client, "invalidateQueries");

    expect(applySocketPayload(client, JOB_ID, JSON.stringify(MESSAGE))).toBe(true);
    expect(client.getQueryData(queryKeys.messages(JOB_ID))).toHaveLength(1);
    expect(invalidate).toHaveBeenCalledWith({ queryKey: queryKeys.unreadMessages });
  });
});

describe("unread badge", () => {
  it("adds up unread messages across conversations", () => {
    expect(unreadTotal(undefined)).toBe(0);
    expect(
      unreadTotal([
        {
          job_id: JOB_ID,
          unread_count: 2,
          last_message_at: null,
          last_message_preview: null,
          last_sender_id: null,
        },
        {
          job_id: MESSAGE.id,
          unread_count: 3,
          last_message_at: null,
          last_message_preview: null,
          last_sender_id: null,
        },
      ]),
    ).toBe(5);
  });

  it("shows the count on the tab and names it for screen readers", () => {
    render(
      <TabBar
        ariaLabel="Worker navigation"
        items={[
          { href: "/worker", label: "Find jobs", icon: "search" },
          { href: "/worker/messages", label: "Messages", icon: "chat", badge: 4 },
        ]}
      />,
    );
    expect(screen.getByRole("link", { name: "Messages, 4 unread" })).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Find jobs" })).toBeInTheDocument();
  });
});
