import { useEffect, useState } from "react";
import {
  useMutation,
  useQuery,
  useQueryClient,
  type QueryClient,
  type UseQueryResult,
} from "@tanstack/react-query";
import { z } from "zod";

import { fetchMessages, markMessagesRead, type SendMessageInput } from "@/core/api/endpoints";
import { messageSchema, type Message } from "@/core/api/schemas";
import { useOnlineStatus } from "@/core/offline/use-online-status";
import { mutationKeys, queryKeys } from "@/core/query/keys";

/** Poll only as a fallback when the live socket is down — data bundles are small. */
const FALLBACK_POLL_MS = 15_000;

export function useMessages(jobId: string, isLive: boolean): UseQueryResult<Message[]> {
  return useQuery({
    queryKey: queryKeys.messages(jobId),
    queryFn: () => fetchMessages(jobId),
    refetchInterval: isLive ? false : FALLBACK_POLL_MS,
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
    },
  });
}

export function useMarkMessagesRead(jobId: string, latestIncomingId: string | undefined): void {
  useEffect(() => {
    if (latestIncomingId === undefined) return;
    markMessagesRead(jobId).catch(() => undefined);
  }, [jobId, latestIncomingId]);
}

const socketTokenSchema = z.object({ token: z.string().min(1) });

function socketBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_WS_URL;
  if (configured) return configured.replace(/\/+$/, "");
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.hostname}:8000`;
}

function applySocketPayload(queryClient: QueryClient, jobId: string, raw: string): void {
  let parsed: ReturnType<typeof messageSchema.safeParse>;
  try {
    parsed = messageSchema.safeParse(JSON.parse(raw));
  } catch {
    void queryClient.invalidateQueries({ queryKey: queryKeys.messages(jobId) });
    return;
  }
  if (parsed.success) {
    queryClient.setQueryData<Message[]>(queryKeys.messages(jobId), (existing) =>
      mergeMessage(existing, parsed.data),
    );
  } else {
    void queryClient.invalidateQueries({ queryKey: queryKeys.messages(jobId) });
  }
}

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

    async function connect(): Promise<void> {
      try {
        const response = await fetch("/api/session/socket-token", { credentials: "same-origin" });
        if (!response.ok || isCancelled) return;
        const { token } = socketTokenSchema.parse(await response.json());
        const url = `${socketBaseUrl()}/jobs/${encodeURIComponent(jobId)}/ws?token=${encodeURIComponent(token)}`;
        socket = new WebSocket(url);
        socket.onopen = () => {
          attempt = 0;
          setIsConnected(true);
        };
        socket.onmessage = (event: MessageEvent<string>) => {
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
      socket?.close();
      setIsConnected(false);
    };
  }, [jobId, isOnline, queryClient]);

  return isConnected;
}
