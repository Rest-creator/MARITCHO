import Link from "next/link";

import { Icon } from "@/components/ui/Icon";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/States";
import type { ConversationUnread, Job } from "@/core/api/schemas";
import { formatRelativeTime, jobStatusLabel } from "@/core/format/format";
import { tradeIcon, tradeLabel } from "@/core/format/trades";
import { splitTiming } from "@/features/jobs/job-helpers";
import { useUnreadMessages } from "@/features/messaging/hooks";

export type ConversationJob = Pick<
  Job,
  "id" | "trade" | "suburb" | "status" | "updated_at" | "problem_description" | "worker_id"
> & {
  offer_count?: number;
  has_offer?: boolean;
};

type Props = {
  jobs: readonly ConversationJob[] | undefined;
  isPending: boolean;
  error: Error | null;
  onRetry: () => void;
  emptyHint: string;
};

/**
 * Chats exist per hired job or job with an active offer — one row per
 * conversation, newest message first, with unread counts. (Sorting by the
 * job's `updated_at` never moved for new messages.)
 */
export function ConversationList({ jobs, isPending, error, onRetry, emptyHint }: Props) {
  const unread = useUnreadMessages();
  const byJob = new Map<string, ConversationUnread>(
    (unread.data ?? []).map((item) => [item.job_id, item]),
  );
  const lastActivity = (job: ConversationJob): string =>
    byJob.get(job.id)?.last_message_at ?? job.updated_at;
  const withChat = (jobs ?? [])
    .filter((job) => job.worker_id !== null || (job.offer_count ?? 0) > 0 || job.has_offer === true)
    .sort((a, b) => lastActivity(b).localeCompare(lastActivity(a)));

  if (isPending) return <Skeleton height={72} count={3} />;
  if (error && !jobs) return <ErrorState message={error.message} onRetry={onRetry} />;
  if (withChat.length === 0) {
    return (
      <EmptyState title="No conversations yet" icon="chat">
        {emptyHint}
      </EmptyState>
    );
  }

  return (
    <ul className="stack" style={{ listStyle: "none", margin: 0, padding: 0 }}>
      {withChat.map((job) => {
        const statusText =
          job.worker_id !== null
            ? jobStatusLabel(job.status)
            : (job.offer_count ?? 0) > 0
              ? `${job.offer_count} ${job.offer_count === 1 ? "offer" : "offers"}`
              : "Offer sent";
        const conversation: ConversationUnread | undefined = byJob.get(job.id);
        const unreadCount: number = conversation?.unread_count ?? 0;
        return (
          <li key={job.id}>
            <Link
              href={`/chat/${job.id}`}
              className={unreadCount > 0 ? "list-row list-row--unread" : "list-row"}
              aria-label={
                unreadCount > 0
                  ? `${tradeLabel(job.trade)} in ${job.suburb}, ${unreadCount} unread`
                  : undefined
              }
            >
              <div className="icon-tile icon-tile--amber">
                <Icon name={tradeIcon(job.trade)} />
              </div>
              <div className="grow" style={{ minWidth: 0 }}>
                <div style={{ fontSize: 15, fontWeight: 700 }} className="truncate">
                  {splitTiming(job.problem_description).text.split("\n")[0] ||
                    tradeLabel(job.trade)}
                </div>
                <div className="meta truncate">
                  {conversation?.last_message_preview ??
                    `${tradeLabel(job.trade)} · ${job.suburb} · ${statusText}`}
                </div>
              </div>
              <div className="stack" style={{ gap: 4, alignItems: "flex-end" }}>
                <span className="meta">{formatRelativeTime(lastActivity(job))}</span>
                {unreadCount > 0 && (
                  <span className="unread-count" aria-hidden="true">
                    {unreadCount > 99 ? "99+" : unreadCount}
                  </span>
                )}
              </div>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
