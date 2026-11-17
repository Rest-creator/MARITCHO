import { useEffect, useState } from "react";
import {
  useMutation,
  useQuery,
  useQueryClient,
  type QueryClient,
  type UseQueryResult,
} from "@tanstack/react-query";
import { z } from "zod";

import {
  fetchMessages,
  fetchUnreadSummary,
  markMessagesRead,
  type SendMessageInput,
} from "@/core/api/endpoints";
import { messageSchema, type ConversationUnread, type Message } from "@/core/api/schemas";
import { useOnlineStatus } from "@/core/offline/use-online-status";
import { mutationKeys, queryKeys } from "@/core/query/keys";

/** Poll as a fallback when the live socket is down, and reconcile periodically when live. */
const FALLBACK_POLL_MS = 4_000;
const LIVE_RECONCILE_MS = 12_000;

export function useMessages(jobId: string, isLive: boolean): UseQueryResult<Message[]> {
  return useQuery({
    queryKey: queryKeys.messages(jobId),
    queryFn: () => fetchMessages(jobId),
    staleTime: 0,
    refetchOnWindowFocus: true,
    refetchInterval: isLive ? LIVE_RECONCILE_MS : FALLBACK_POLL_MS,
  });
}

/** Insert or replace by id, keeping chronological order. */
export function mergeMessage(
  existing: readonly Message[] | undefined,
  incoming: Message,
): Message[] {
  const withoutDuplicate = (existing ?? []).filter((message) => message.id !== incoming.id);
  return [...withoutDuplicate, incoming].sort((a, b) => a.created_at.localeCompare(b.created_at));
}

export function useSendMessage(jobId: string) {
  const queryClient = useQueryClient();
  return useMutation<Message, Error, SendMessageInput>({
    mutationKey: mutationKeys.sendMessage,
    onSuccess: (message) => {
      queryClient.setQueryData<Message[]>(queryKeys.messages(jobId), (existing) =>
        mergeMessage(existing, message),
      );
      void queryClient.invalidateQueries({ queryKey: queryKeys.myJobs });
      void queryClient.invalidateQueries({ queryKey: queryKeys.assignedJobs });
      void queryClient.invalidateQueries({ queryKey: queryKeys.myOffers });
      void queryClient.invalidateQueries({ queryKey: queryKeys.unreadMessages });
    },
  });
}

/**
 * Marks the thread read, but only while the person can actually see it: a
 * chat left open in a background tab no longer swallows new messages
 * (which also cleared the sender's "unread" before anyone looked).
 */
export function useMarkMessagesRead(jobId: string, latestIncomingId: string | undefined): void {
  const queryClient = useQueryClient();
  useEffect(() => {
    if (latestIncomingId === undefined) return undefined;

    function markRead(): void {
      markMessagesRead(jobId)
        .then(() => queryClient.invalidateQueries({ queryKey: queryKeys.unreadMessages }))
        .catch(() => undefined);
    }

    if (document.visibilityState === "visible") {
      markRead();
      return undefined;
    }
    function handleVisible(): void {
      if (document.visibilityState !== "visible") return;
      document.removeEventListener("visibilitychange", handleVisible);
      markRead();
    }
    document.addEventListener("visibilitychange", handleVisible);
    return () => document.removeEventListener("visibilitychange", handleVisible);
  }, [jobId, latestIncomingId, queryClient]);
}

/** How often the badge checks for new messages when no chat is open. */
const UNREAD_POLL_MS = 30_000;

/**
 * Unread counts across all conversations: drives the Messages badge, the
 * tab title and inbox order. Polls gently (and on focus) because new
 * messages for chats that aren't open have no other way in.
 */
export function useUnreadMessages(isEnabled: boolean = true): UseQueryResult<ConversationUnread[]> {
  return useQuery({
    queryKey: queryKeys.unreadMessages,
    queryFn: ({ signal }) => fetchUnreadSummary(signal),
    enabled: isEnabled,
    staleTime: 10_000,
    refetchInterval: UNREAD_POLL_MS,
    refetchIntervalInBackground: false,
    refetchOnWindowFocus: true,
  });
}

export function unreadTotal(summary: readonly ConversationUnread[] | undefined): number {
  return (summary ?? []).reduce((total, item) => total + item.unread_count, 0);
}

/** "(3) Maritcho": the unread count in the browser tab / task switcher. */
export function useUnreadDocumentTitle(total: number): void {
  useEffect(() => {
    const base: string = document.title.replace(/^\(\d+\+?\)\s*/, "");
    document.title = total > 0 ? `(${total > 99 ? "99+" : total}) ${base}` : base;
  }, [total]);
}

const socketTokenSchema = z.object({ token: z.string().min(1) });

function socketBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_WS_URL;
  if (configured) return configured.replace(/\/+$/, "");
  if (window.location.protocol === "https:") {
    return `wss://${window.location.host}`;
  }
  return `ws://${window.location.hostname}:8000`;
}

const heartbeatSchema = z.object({ type: z.literal("ping") });

/** Applies one socket frame. Returns false for heartbeats (no data). */
export function applySocketPayload(queryClient: QueryClient, jobId: string, raw: string): boolean {
  let payload: unknown;
  try {
    payload = JSON.parse(raw);
  } catch {
    void queryClient.invalidateQueries({ queryKey: queryKeys.messages(jobId) });
    return true;
  }
  if (heartbeatSchema.safeParse(payload).success) return false;

  const parsed = messageSchema.safeParse(payload);
  if (parsed.success) {
    queryClient.setQueryData<Message[]>(queryKeys.messages(jobId), (existing) =>
      mergeMessage(existing, parsed.data),
    );
  } else {
    void queryClient.invalidateQueries({ queryKey: queryKeys.messages(jobId) });
  }
  void queryClient.invalidateQueries({ queryKey: queryKeys.unreadMessages });
  return true;
}

/** The server pings every 25 s; silence this long means the socket is dead. */
const SOCKET_SILENCE_MS = 60_000;

/**
 * Live push of new messages (receive-only — sending always goes through
 * POST /messages). Returns whether the socket is currently connected so
 * the caller can fall back to polling.
 */
export function useChatSocket(jobId: string): boolean {
  const queryClient = useQueryClient();
  const isOnline = useOnlineStatus();
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (!isOnline) return;
    let socket: WebSocket | null = null;
    let isCancelled = false;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;
    let attempt = 0;
    let lastFrameAt = Date.now();
    // Mobile networks drop idle sockets without telling either side; close a
    // silent one so onclose reconnects instead of "live" with nothing arriving.
    const watchdog = setInterval(() => {
      if (socket?.readyState === WebSocket.OPEN && Date.now() - lastFrameAt > SOCKET_SILENCE_MS) {
        socket.close();
      }
    }, SOCKET_SILENCE_MS / 4);

    async function connect(): Promise<void> {
      try {
        const response = await fetch("/api/session/socket-token", { credentials: "same-origin" });
        if (!response.ok || isCancelled) return;
        const { token } = socketTokenSchema.parse(await response.json());
        const url = `${socketBaseUrl()}/jobs/${encodeURIComponent(jobId)}/ws?token=${encodeURIComponent(token)}`;
        socket = new WebSocket(url);
        socket.onopen = () => {
          attempt = 0;
          lastFrameAt = Date.now();
          setIsConnected(true);
          void queryClient.invalidateQueries({ queryKey: queryKeys.messages(jobId) });
        };
        socket.onmessage = (event: MessageEvent<string>) => {
          lastFrameAt = Date.now();
          applySocketPayload(queryClient, jobId, event.data);
        };
        socket.onclose = (event: CloseEvent) => {
          setIsConnected(false);
          // 44xx = auth / not found / forbidden — retrying won't help.
          if (isCancelled || (event.code >= 4400 && event.code < 4500)) return;
          attempt += 1;
          retryTimer = setTimeout(() => void connect(), Math.min(30_000, 1000 * 2 ** attempt));
        };
      } catch {
        setIsConnected(false);
      }
    }

    void connect();
    return () => {
      isCancelled = true;
      clearTimeout(retryTimer);
      clearInterval(watchdog);
      socket?.close();
      setIsConnected(false);
    };
  }, [jobId, isOnline, queryClient]);

  return isConnected;
}
