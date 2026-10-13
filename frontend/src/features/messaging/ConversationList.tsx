import Link from "next/link";

import { Icon } from "@/components/ui/Icon";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/States";
import type { Job } from "@/core/api/schemas";
import { formatRelativeTime, jobStatusLabel } from "@/core/format/format";
import { tradeIcon, tradeLabel } from "@/core/format/trades";
import { splitTiming } from "@/features/jobs/job-helpers";

type ConversationJob = Pick<
  Job,
  "id" | "trade" | "suburb" | "status" | "updated_at" | "problem_description" | "worker_id"
>;

type Props = {
  jobs: readonly ConversationJob[] | undefined;
  isPending: boolean;
  error: Error | null;
  onRetry: () => void;
  emptyHint: string;
};

/** Chats exist per hired job — one row per job with someone on it. */
export function ConversationList({ jobs, isPending, error, onRetry, emptyHint }: Props) {
  const withChat = (jobs ?? [])
    .filter((job) => job.worker_id !== null)
    .sort((a, b) => b.updated_at.localeCompare(a.updated_at));

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
      {withChat.map((job) => (
        <li key={job.id}>
          <Link href={`/chat/${job.id}`} className="list-row">
            <div className="icon-tile icon-tile--amber">
              <Icon name={tradeIcon(job.trade)} />
            </div>
            <div className="grow">
              <div style={{ fontSize: 15, fontWeight: 700 }} className="truncate">
                {splitTiming(job.problem_description).text.split("\n")[0] || tradeLabel(job.trade)}
              </div>
              <div className="meta truncate">
                {tradeLabel(job.trade)} · {job.suburb} · {jobStatusLabel(job.status)}
              </div>
            </div>
            <span className="meta">{formatRelativeTime(job.updated_at)}</span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
