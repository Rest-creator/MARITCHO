import Link from "next/link";

import { Avatar } from "@/components/ui/Avatar";
import { Icon } from "@/components/ui/Icon";
import type { Job, MatchCandidate } from "@/core/api/schemas";
import { formatKm, formatMoney, formatPercent, isVerifiedGrade } from "@/core/format/format";
import { tradeLabel } from "@/core/format/trades";
import { candidateTitle } from "@/features/jobs/job-helpers";

type Props = {
  job: Job;
  candidate: MatchCandidate;
  isTopPick: boolean;
  onHire: (candidate: MatchCandidate) => void;
};

/** One person who offered to help (design E4). */
export function CandidateCard({ job, candidate, isTopPick, onHire }: Props) {
  const title = candidateTitle(candidate, job.trade);
  const availability = candidate.availability_note ?? candidate.reason;

  return (
    <article
      className={isTopPick ? "card card--amber" : "card card--bold"}
      style={isTopPick ? undefined : { background: "var(--glass)" }}
    >
      <div className="row row--start">
        <Avatar name={title} seed={candidate.worker_id} size="md" />
        <div className="grow">
          <div className="row row--tight">
            <h3 style={{ fontSize: 16, fontWeight: 700 }}>{title}</h3>
            {isVerifiedGrade(candidate.grade) && (
              <span className="text-emerald" style={{ display: "flex" }}>
                <Icon name="shieldCheck" size={16} label="Checked by Maricho" />
              </span>
            )}
          </div>
          <div className="meta meta--secondary" style={{ marginTop: 3 }}>
            {tradeLabel(job.trade)} · {formatKm(candidate.distance_km)} away · {availability}
          </div>
          <div className="row meta meta--secondary" style={{ marginTop: 6, gap: 10 }}>
            {candidate.jobs_completed === 0 ? (
              <span>No jobs on Maricho yet</span>
            ) : (
              <>
                <span className="rating">
                  <Icon name="clock" size={12} strokeWidth={2.4} />
                  {formatPercent(candidate.on_time_rate)} on time
                </span>
                <span>{candidate.jobs_completed} jobs done</span>
              </>
            )}
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: 18, fontWeight: 700 }}>
            {candidate.quoted_amount === null ? "—" : formatMoney(candidate.quoted_amount)}
          </div>
          <div className="meta" style={{ fontSize: 11 }}>
            {candidate.quoted_amount === null ? "no quote yet" : "quote"}
          </div>
        </div>
      </div>
      <div className="btn-grid" style={{ marginTop: 14 }}>
        <Link href={`/employer/jobs/${job.id}/workers/${candidate.worker_id}`} className="btn">
          View profile
        </Link>
        <button
          type="button"
          className={isTopPick ? "btn btn--primary" : "btn btn--soft"}
          onClick={() => onHire(candidate)}
        >
          Hire
        </button>
      </div>
    </article>
  );
}
