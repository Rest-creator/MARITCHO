import Link from "next/link";

import { Icon } from "@/components/ui/Icon";
import type { OpenJob } from "@/core/api/schemas";
import { formatKm, formatMoney, formatRelativeTime } from "@/core/format/format";
import { tradeIcon, tradeLabel } from "@/core/format/trades";
import { splitTiming } from "@/features/jobs/job-helpers";

type Props = { job: OpenJob; isFeatured: boolean; hasOffered: boolean };

/** A job card on W2 — the first one is emphasised, as in the design. */
export function OpenJobCard({ job, isFeatured, hasOffered }: Props) {
  const { text, timing } = splitTiming(job.problem_description);
  const title = text.split("\n")[0] || tradeLabel(job.trade);
  const href = `/worker/jobs/${job.job_id}`;

  return (
    <article
      className={isFeatured ? "card card--bold" : "card"}
      style={isFeatured ? undefined : { background: "var(--glass)", borderColor: "var(--line)" }}
    >
      <div className="row row--start">
        <div className={isFeatured ? "icon-tile icon-tile--amber" : "icon-tile icon-tile--emerald"}>
          <Icon name={tradeIcon(job.trade)} />
        </div>
        <div className="grow">
          <div className="row row--between row--start" style={{ gap: 8 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, lineHeight: 1.3 }}>{title}</h3>
            <div style={{ fontSize: 15, fontWeight: 700, whiteSpace: "nowrap" }}>
              {job.budget_amount === null ? "Make an offer" : formatMoney(job.budget_amount)}
            </div>
          </div>
          <div className="meta meta--secondary" style={{ marginTop: 4 }}>
            {job.suburb} · {formatKm(job.distance_km)}
            {timing ? ` · ${timing}` : ""}
          </div>
          <div className="meta" style={{ marginTop: 4 }}>
            {tradeLabel(job.trade)} · {formatRelativeTime(job.created_at)}
          </div>
        </div>
      </div>
      <div className="btn-grid" style={{ marginTop: 12 }}>
        <Link href={href} className="btn">
          Details
        </Link>
        <Link href={href} className={isFeatured ? "btn btn--primary" : "btn btn--soft"}>
          {hasOffered ? "Update offer" : "I can do this"}
        </Link>
      </div>
    </article>
  );
}
