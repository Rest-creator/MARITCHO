import Link from "next/link";

import { Icon } from "@/components/ui/Icon";
import type { MyJob } from "@/core/api/schemas";
import { formatRelativeTime, formatShortDate, jobStatusLabel } from "@/core/format/format";
import { tradeIcon, tradeLabel } from "@/core/format/trades";
import { employerJobHref, isOpenStatus, splitTiming } from "@/features/jobs/job-helpers";

type Props = { job: MyJob };

/** "Your jobs" card on E1 — open jobs invite review, the rest show progress. */
export function EmployerJobCard({ job }: Props) {
  const title = splitTiming(job.problem_description).text.split("\n")[0] || tradeLabel(job.trade);

  if (job.status === "COMPLETED") {
    return (
      <div
        className="list-row"
        style={{ background: "var(--glass-faint)", borderColor: "var(--line-faint)" }}
      >
        <div className="icon-tile icon-tile--sm icon-tile--emerald">
          <Icon name="check" />
        </div>
        <div className="grow">
          <div style={{ fontSize: 14, fontWeight: 600 }} className="truncate">
            {title}
          </div>
          <div className="meta">
            {tradeLabel(job.trade)} · Done {formatShortDate(job.updated_at)}
          </div>
        </div>
        <Link
          href={`/employer/post?trade=${job.trade}`}
          className="meta meta--secondary"
          style={{ fontWeight: 600 }}
        >
          Hire again
        </Link>
      </div>
    );
  }

  const isOpen = isOpenStatus(job.status);
  const badge = isOpen
    ? `${job.offer_count} ${job.offer_count === 1 ? "offer" : "offers"}`
    : jobStatusLabel(job.status);

  return (
    <Link href={employerJobHref(job)} className="card">
      <div className="row">
        <div className="icon-tile icon-tile--sm icon-tile--amber">
          <Icon name={tradeIcon(job.trade)} />
        </div>
        <div className="grow">
          <div style={{ fontSize: 15, fontWeight: 700 }}>{title}</div>
          <div className="meta">
            {tradeLabel(job.trade)} · Posted {formatRelativeTime(job.created_at)}
          </div>
        </div>
        <span className={isOpen ? "badge badge--amber" : "badge badge--emerald"}>{badge}</span>
      </div>
      <div className="card__divider row row--between">
        <span className="meta meta--secondary">{job.suburb}</span>
        <span
          className="row row--tight text-amber"
          style={{ fontSize: 13, fontWeight: 600, gap: 4 }}
        >
          {isOpen ? "Review offers" : "See progress"}
          <Icon name="chevronRight" size={16} strokeWidth={2} />
        </span>
      </div>
    </Link>
  );
}
