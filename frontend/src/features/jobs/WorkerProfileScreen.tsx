"use client";

import { useState } from "react";
import Link from "next/link";

import { Avatar } from "@/components/ui/Avatar";
import { BackButton } from "@/components/ui/BackButton";
import { Icon } from "@/components/ui/Icon";
import { Screen } from "@/components/ui/Screen";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/States";
import {
  distanceBandLabel,
  formatKm,
  formatMoney,
  formatPercent,
  gradeLabel,
  isVerifiedGrade,
} from "@/core/format/format";
import { tradeLabel } from "@/core/format/trades";
import { HireSheet } from "@/features/jobs/HireSheet";
import { useJob, useMatches } from "@/features/jobs/hooks";
import {
  candidatePrice,
  candidateTitle,
  isOpenStatus,
  matchExplanation,
} from "@/features/jobs/job-helpers";

type Props = { jobId: string; workerId: string };

/**
 * Design E5 · Worker profile & references, built from the matching
 * engine's view of this worker for this job (the backend has no public
 * worker-profile endpoint yet, so past-work photos and written reviews
 * are not shown).
 */
export function WorkerProfileScreen({ jobId, workerId }: Props) {
  const job = useJob(jobId);
  const matches = useMatches(jobId, job.data ? isOpenStatus(job.data.status) : false);
  const [isHiring, setIsHiring] = useState(false);
  const candidate = matches.data?.find((item) => item.worker_id === workerId);

  if (job.isPending || matches.isPending) {
    return (
      <Screen>
        <Skeleton height={190} />
        <Skeleton height={80} count={3} />
      </Screen>
    );
  }

  const loadError = job.error ?? matches.error;
  if (!job.data || !candidate) {
    return (
      <Screen>
        <div className="topbar">
          <BackButton fallbackHref={`/employer/jobs/${jobId}`} />
        </div>
        {loadError ? (
          <ErrorState message={loadError.message} />
        ) : (
          <EmptyState title="This offer is no longer open" icon="user">
            The worker may have taken another job. Go back to see who else can help.
          </EmptyState>
        )}
      </Screen>
    );
  }

  const title = candidateTitle(candidate, job.data.trade);
  const price = candidatePrice(candidate, job.data);
  const hasHistory = candidate.jobs_completed > 0;

  return (
    <Screen glow="worker" isPadded={false}>
      <div className="cover">
        <BackButton fallbackHref={`/employer/jobs/${jobId}`} isOverlay />
      </div>
      <main className="profile-body">
        <div className="row" style={{ alignItems: "flex-end", gap: 14 }}>
          <Avatar name={title} seed={candidate.worker_id} size="xl" />
          <div className="grow" style={{ paddingBottom: 6 }}>
            <div className="row row--tight">
              <h1 style={{ fontSize: 21, fontWeight: 700 }}>{title}</h1>
              {isVerifiedGrade(candidate.grade) && (
                <span className="text-emerald" style={{ display: "flex" }}>
                  <Icon name="shieldCheck" size={18} label="Checked by Maricho" />
                </span>
              )}
            </div>
            <div className="meta meta--secondary" style={{ fontSize: 13 }}>
              {tradeLabel(job.data.trade)} · {candidate.suburb}
            </div>
          </div>
        </div>

        <div className="stat-grid">
          <div className="stat-tile">
            <div className="stat__value text-amber">
              {hasHistory ? formatPercent(candidate.on_time_rate) : "New"}
            </div>
            <div className="stat__label">On time</div>
          </div>
          <div className="stat-tile">
            <div className="stat__value">{candidate.jobs_completed}</div>
            <div className="stat__label">Jobs done</div>
          </div>
          <div className="stat-tile">
            <div className="stat__value">
              {hasHistory ? formatPercent(candidate.fill_rate) : "—"}
            </div>
            <div className="stat__label">Shows up</div>
          </div>
        </div>

        <section>
          <h2 style={{ fontSize: 14, fontWeight: 700 }}>Checked by Maricho</h2>
          <div className="chip-list" style={{ marginTop: 8, gap: 6 }}>
            <span className={isVerifiedGrade(candidate.grade) ? "tag tag--verified" : "tag"}>
              {isVerifiedGrade(candidate.grade) && (
                <Icon name="check" size={12} strokeWidth={2.4} />
              )}
              {gradeLabel(candidate.grade)} · {tradeLabel(job.data.trade)}
            </span>
            {hasHistory && (
              <span className="tag">{formatPercent(candidate.dispute_rate)} of jobs disputed</span>
            )}
            {candidate.travel_means && (
              <span className="tag">Travels by {candidate.travel_means}</span>
            )}
          </div>
        </section>

        <section className="card" style={{ padding: 14, borderRadius: 16 }}>
          <div className="row row--between">
            <h2 style={{ fontSize: 13, fontWeight: 700 }}>Why we matched them</h2>
            <span className="meta">
              {distanceBandLabel(candidate.distance_band)} · {formatKm(candidate.distance_km)}
            </span>
          </div>
          <p
            className="meta meta--secondary"
            style={{ marginTop: 8, fontSize: 13, lineHeight: 1.5 }}
          >
            {matchExplanation(candidate, job.data.trade)}
          </p>
          {candidate.availability_note && (
            <div
              className="row row--tight text-emerald"
              style={{ marginTop: 8, fontSize: 11, gap: 5 }}
            >
              <Icon name="clock" size={12} />
              {candidate.availability_note}
            </div>
          )}
        </section>
      </main>

      <div className="action-bar">
        <Link
          href={`/employer/jobs/${jobId}`}
          className="btn"
          style={{ height: 54, borderRadius: 16, fontSize: 15 }}
        >
          Compare
        </Link>
        <button
          type="button"
          className="btn btn--primary"
          style={{ height: 54, borderRadius: 16, fontSize: 16 }}
          onClick={() => setIsHiring(true)}
        >
          Hire{price === null ? "" : ` · ${formatMoney(price)}`}
        </button>
      </div>

      {isHiring && (
        <HireSheet job={job.data} candidate={candidate} onClose={() => setIsHiring(false)} />
      )}
    </Screen>
  );
}
