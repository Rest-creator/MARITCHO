"use client";

import Link from "next/link";

import { Avatar } from "@/components/ui/Avatar";
import { BackButton } from "@/components/ui/BackButton";
import { Icon } from "@/components/ui/Icon";
import { Screen } from "@/components/ui/Screen";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/States";
import { TapToLoadPhoto } from "@/components/ui/TapToLoadPhoto";
import {
  distanceBandLabel,
  formatKm,
  formatPercent,
  gradeLabel,
  isVerifiedGrade,
} from "@/core/format/format";
import { tradeIcon, tradeLabel } from "@/core/format/trades";
import { useLocalProfile } from "@/core/session/profile-store";
import { candidateTitle } from "@/features/jobs/job-helpers";
import { useWorkerProfile } from "@/features/workers/hooks";

type Props = {
  workerId: string;
  initialSuburb?: string | null;
};

/** Public worker profile opened from the Employer Workers directory. */
export function WorkerPublicProfileScreen({ workerId, initialSuburb }: Props) {
  const localProfile = useLocalProfile();
  const originSuburb =
    initialSuburb?.trim() || localProfile.lastSuburb || localProfile.homeSuburb || "";
  const profile = useWorkerProfile(workerId, originSuburb);

  if (profile.isPending) {
    return (
      <Screen>
        <Skeleton height={190} />
        <Skeleton height={80} count={3} />
      </Screen>
    );
  }

  if (!profile.data) {
    return (
      <Screen>
        <div className="topbar">
          <BackButton fallbackHref="/employer/workers" />
        </div>
        {profile.error ? (
          <ErrorState message={profile.error.message} onRetry={() => void profile.refetch()} />
        ) : (
          <EmptyState title="Worker not found" icon="user">
            Go back to the workers list to browse people near you.
          </EmptyState>
        )}
      </Screen>
    );
  }

  const worker = profile.data;
  const primaryTrade = worker.trades[0] ?? "BUILDING";
  const title = candidateTitle(
    { grade: worker.grade, display_name: worker.display_name },
    primaryTrade,
  );
  const hasHistory = worker.jobs_completed > 0;

  return (
    <Screen glow="worker" isPadded={false}>
      <div className="cover">
        <BackButton fallbackHref="/employer/workers" isOverlay />
      </div>
      <main className="profile-body">
        <div className="row" style={{ alignItems: "flex-end", gap: 14 }}>
          <Avatar name={title} seed={worker.worker_id} size="xl" isOnline={worker.is_available} />
          <div className="grow" style={{ paddingBottom: 6 }}>
            <div className="row row--tight">
              <h1 style={{ fontSize: 21, fontWeight: 700 }}>{title}</h1>
              {isVerifiedGrade(worker.grade) && (
                <span className="text-emerald" style={{ display: "flex" }}>
                  <Icon name="shieldCheck" size={18} label="Checked by Maricho" />
                </span>
              )}
            </div>
            <div className="meta meta--secondary" style={{ fontSize: 13 }}>
              {worker.trades.map((trade) => tradeLabel(trade)).join(" · ") ||
                tradeLabel(primaryTrade)}{" "}
              · {worker.suburb ?? "Bulawayo"}
            </div>
          </div>
        </div>

        <div className="stat-grid">
          <div className="stat-tile">
            <div className="stat__value text-amber">
              {hasHistory ? formatPercent(worker.on_time_rate) : "New"}
            </div>
            <div className="stat__label">On time</div>
          </div>
          <div className="stat-tile">
            <div className="stat__value">{worker.jobs_completed}</div>
            <div className="stat__label">Jobs done</div>
          </div>
          <div className="stat-tile">
            <div className="stat__value">
              {worker.rating_average !== null && worker.rating_average !== undefined
                ? `★ ${worker.rating_average.toFixed(1)}`
                : hasHistory
                  ? formatPercent(worker.fill_rate)
                  : "—"}
            </div>
            <div className="stat__label">
              {worker.rating_average !== null && worker.rating_average !== undefined
                ? `Rating (${worker.rating_count ?? 0})`
                : "Shows up"}
            </div>
          </div>
        </div>

        <section>
          <h2 style={{ fontSize: 14, fontWeight: 700 }}>Skills &amp; vetting</h2>
          <div className="chip-list" style={{ marginTop: 8, gap: 6 }}>
            <span className={isVerifiedGrade(worker.grade) ? "tag tag--verified" : "tag"}>
              {isVerifiedGrade(worker.grade) && <Icon name="check" size={12} strokeWidth={2.4} />}
              {gradeLabel(worker.grade)}
            </span>
            {worker.trades.map((trade) => (
              <span key={trade} className="tag">
                <Icon name={tradeIcon(trade)} size={13} />
                {tradeLabel(trade)}
              </span>
            ))}
            {worker.reference_count > 0 && (
              <span className="tag">
                {worker.reference_count} reference{worker.reference_count === 1 ? "" : "s"} checked
              </span>
            )}
            {hasHistory && (
              <span className="tag">{formatPercent(worker.dispute_rate)} of jobs disputed</span>
            )}
          </div>
        </section>

        <section className="card" style={{ padding: 14, borderRadius: 16 }}>
          <div className="row row--between">
            <h2 style={{ fontSize: 13, fontWeight: 700 }}>Where they work</h2>
            {worker.distance_band && (
              <span className="meta">
                {distanceBandLabel(worker.distance_band)}
                {worker.distance_km !== null && worker.distance_km !== undefined
                  ? ` · ${formatKm(worker.distance_km)}`
                  : ""}
              </span>
            )}
          </div>
          <p
            className="meta meta--secondary"
            style={{ marginTop: 8, fontSize: 13, lineHeight: 1.5 }}
          >
            Covers{" "}
            {worker.service_areas.length > 0
              ? worker.service_areas.join(", ")
              : (worker.suburb ?? "local suburbs")}{" "}
            (up to {worker.travel_km} km)
            {worker.travel_means ? ` · travels by ${worker.travel_means.toLowerCase()}` : ""}.
          </p>
        </section>

        {worker.proof_urls.length > 0 && (
          <section className="stack" style={{ gap: 8 }}>
            <h2 style={{ fontSize: 14, fontWeight: 700 }}>Photos of past work</h2>
            <div className="stack" style={{ gap: 8 }}>
              {worker.proof_urls.map((url) => (
                <TapToLoadPhoto key={url} url={url} alt={`${title}'s work`} />
              ))}
            </div>
          </section>
        )}

        {worker.recent_work.length > 0 && (
          <section className="stack" style={{ gap: 8 }}>
            <h2 style={{ fontSize: 14, fontWeight: 700 }}>Signed-off jobs on Maricho</h2>
            {worker.recent_work.map((record) => (
              <article key={record.job_id} className="card card--compact stack" style={{ gap: 6 }}>
                <div style={{ fontSize: 14, fontWeight: 700 }}>{record.what_was_done}</div>
                {record.client_words && (
                  <p className="meta meta--secondary" style={{ lineHeight: 1.45 }}>
                    “{record.client_words}”
                  </p>
                )}
              </article>
            ))}
          </section>
        )}
      </main>

      <div className="action-bar">
        <Link
          href="/employer/workers"
          className="btn"
          style={{ height: 54, borderRadius: 16, fontSize: 15 }}
        >
          All workers
        </Link>
        <Link
          href={`/employer/post?trade=${primaryTrade}`}
          className="btn btn--primary"
          style={{ height: 54, borderRadius: 16, fontSize: 16 }}
        >
          Post {tradeLabel(primaryTrade).toLowerCase()} job
        </Link>
      </div>
    </Screen>
  );
}
