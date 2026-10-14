"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useMutationState } from "@tanstack/react-query";

import { Avatar } from "@/components/ui/Avatar";
import { BackButton } from "@/components/ui/BackButton";
import { Icon } from "@/components/ui/Icon";
import { Screen } from "@/components/ui/Screen";
import { ErrorState, Skeleton } from "@/components/ui/States";
import type { SendMessageInput } from "@/core/api/endpoints";
import type { Message } from "@/core/api/schemas";
import { formatClock, formatDayLabel, formatMoney, jobStatusLabel } from "@/core/format/format";
import { tradeIcon, tradeLabel } from "@/core/format/trades";
import { useMediaUploads } from "@/core/media/use-media-uploads";
import { useOnlineStatus } from "@/core/offline/use-online-status";
import { mutationKeys } from "@/core/query/keys";
import { useSession } from "@/core/session/SessionProvider";
import { useJob } from "@/features/jobs/hooks";
import { splitTiming } from "@/features/jobs/job-helpers";
import { ChatComposer } from "@/features/messaging/ChatComposer";
import { MessageBubble } from "@/features/messaging/MessageBubble";
import {
  useChatSocket,
  useMarkMessagesRead,
  useMessages,
  useSendMessage,
} from "@/features/messaging/hooks";

type Props = { jobId: string };

interface DayGroup {
  label: string;
  messages: Message[];
}

export function groupByDay(messages: readonly Message[], now: Date = new Date()): DayGroup[] {
  const groups: DayGroup[] = [];
  for (const message of messages) {
    const label = formatDayLabel(message.created_at, now);
    const last = groups[groups.length - 1];
    if (last && last.label === label) {
      last.messages.push(message);
    } else {
      groups.push({ label, messages: [message] });
    }
  }
  return groups;
}

/** Design 3 · Messages (both users). */
export function ChatScreen({ jobId }: Props) {
  const { user } = useSession();
  const job = useJob(jobId);
  const isLive = useChatSocket(jobId);
  const messages = useMessages(jobId, isLive);
  const sendMessage = useSendMessage(jobId);
  const canUpload = useMediaUploads();
  const isOnline = useOnlineStatus();
  const [locationError, setLocationError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  const pending = useMutationState<SendMessageInput>({
    filters: { mutationKey: mutationKeys.sendMessage, status: "pending" },
    select: (mutation) => mutation.state.variables as SendMessageInput,
  }).filter((variables) => variables.jobId === jobId);

  const list = messages.data ?? [];
  const latestIncoming = [...list].reverse().find((message) => message.sender_id !== user?.id);
  useMarkMessagesRead(jobId, latestIncoming?.id);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end" });
  }, [list.length, pending.length]);

  const isWorker = user?.role === "WORKER";
  const backHref = isWorker ? "/worker/work" : `/employer/jobs/${jobId}/track`;
  const counterpart = job.data
    ? isWorker
      ? `Client in ${job.data.suburb}`
      : `Your ${tradeLabel(job.data.trade).toLowerCase()}`
    : "Messages";
  const lastMine = [...list].reverse().find((message) => message.sender_id === user?.id);

  const { mutate: send } = sendMessage;
  const handleSend = useCallback(
    (message: Omit<SendMessageInput, "jobId">) => send({ jobId, ...message }),
    [jobId, send],
  );

  function shareLocation(): void {
    setLocationError(null);
    if (!("geolocation" in navigator)) {
      setLocationError("This phone can't share its location.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      ({ coords }) =>
        sendMessage.mutate({
          jobId,
          message_type: "LOCATION",
          latitude: Number(coords.latitude.toFixed(6)),
          longitude: Number(coords.longitude.toFixed(6)),
        }),
      () => setLocationError("Location is off. Turn it on in your phone settings to share it."),
      { enableHighAccuracy: false, timeout: 15_000, maximumAge: 60_000 },
    );
  }

  return (
    <Screen glow="employer" isPadded={false}>
      <div className="chat">
        <header className="chat__header">
          <BackButton fallbackHref={backHref} />
          <Avatar name={counterpart} seed={job.data?.worker_id ?? jobId} isOnline={isLive} />
          <div className="grow">
            <div style={{ fontSize: 16, fontWeight: 700 }} className="truncate">
              {counterpart}
            </div>
            <div className="meta">
              {isLive ? "Connected · messages arrive instantly" : "Messages may take a moment"}
            </div>
          </div>
        </header>

        {job.data && (
          <div
            className="card card--compact row"
            style={{ margin: "12px 16px 0", borderRadius: 14, background: "var(--glass)" }}
          >
            <div className="icon-tile icon-tile--xs icon-tile--amber">
              <Icon name={tradeIcon(job.data.trade)} size={18} />
            </div>
            <div className="grow">
              <div style={{ fontSize: 13, fontWeight: 600 }} className="truncate">
                {splitTiming(job.data.problem_description).text.split("\n")[0] ||
                  tradeLabel(job.data.trade)}
              </div>
              <div className="meta">
                {job.data.suburb}
                {job.data.quote_amount !== null ? ` · ${formatMoney(job.data.quote_amount)}` : ""}
              </div>
            </div>
            <span className="badge badge--emerald">{jobStatusLabel(job.data.status)}</span>
          </div>
        )}

        <div className="chat__thread" aria-live="polite">
          {messages.isPending && <Skeleton height={48} count={3} />}
          {messages.isError && !messages.data && (
            <ErrorState message={messages.error.message} onRetry={() => void messages.refetch()} />
          )}
          {messages.data && list.length === 0 && pending.length === 0 && (
            <p className="chat__day">Say hello — agree on a time and anything they should bring.</p>
          )}
          {groupByDay(list).map((group) => (
            <div key={group.label} className="stack" style={{ gap: 10 }}>
              <div className="chat__day">{group.label}</div>
              {group.messages.map((message) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                  isMine={message.sender_id === user?.id}
                />
              ))}
            </div>
          ))}
          {lastMine && pending.length === 0 && (
            <div className="bubble__receipt">
              {lastMine.read_at
                ? `Read ${formatClock(lastMine.read_at)}`
                : `Sent ${formatClock(lastMine.created_at)}`}
            </div>
          )}
          {pending.map((variables, index) => (
            <MessageBubble
              key={`pending-${index}`}
              isMine
              isPending
              message={{
                message_type: variables.message_type,
                body: variables.body ?? null,
                media_url: variables.media_url ?? null,
                duration_seconds: variables.duration_seconds ?? null,
                latitude: variables.latitude ?? null,
                longitude: variables.longitude ?? null,
              }}
            />
          ))}
          {pending.length > 0 && <div className="bubble__receipt">Sending when connected…</div>}
          <div ref={endRef} />
        </div>

        {locationError && (
          <p className="field-error" role="alert" style={{ padding: "0 16px 8px" }}>
            {locationError}
          </p>
        )}
        <div className="chat__quick">
          <button type="button" className="pill" onClick={shareLocation}>
            Share my location
          </button>
        </div>
        <ChatComposer canAttach={canUpload && isOnline} onSend={handleSend} />
      </div>
    </Screen>
  );
}
