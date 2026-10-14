"use client";

import { useState } from "react";
import Link from "next/link";

import { Icon } from "@/components/ui/Icon";
import { Screen } from "@/components/ui/Screen";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/States";
import {
  formatMoney,
  formatPercent,
  formatRelativeTime,
  formatShortDate,
  jobStatusLabel,
} from "@/core/format/format";
import { tradeLabel } from "@/core/format/trades";
import { isOpenStatus, splitTiming } from "@/features/jobs/job-helpers";
import { ActiveJobCard } from "@/features/worker/ActiveJobCard";
import { monthLabel, summariseMonth } from "@/features/worker/earnings";
import { WorkerTabBar } from "@/features/worker/WorkerTabBar";
import { useWorkerWorkScreen } from "@/features/worker/screen-hooks";

export type WorkTab = "offers" | "active" | "done";

const ACTIVE_STATUSES = new Set(["BOOKED", "IN_PROGRESS", "DISPUTED"]);

type Props = { initialTab: WorkTab };

/** Design W4 · My work, earnings & standing. */
export function MyWorkScreen({ initialTab }: Props) {
  // One request for the whole screen (ADR-009 phase 2).
  const screen = useWorkerWorkScreen();
  const standing = screen.data?.standing;
  const [tab, setTab] = useState<WorkTab>(initialTab);

  const jobs = screen.data?.assigned ?? [];
  const activeJobs = jobs.filter((job) => ACTIVE_STATUSES.has(job.status));
  const doneJobs = jobs.filter((job) => job.status === "COMPLETED");
  const offers = screen.data?.offers ?? [];
  const openOffers = offers.filter((offer) => isOpenStatus(offer.job_status));
  const offerByJob = new Map(offers.map((offer) => [offer.job_id, offer.quoted_amount]));
  const month = summariseMonth(jobs);
  const isLoading = screen.isPending;
  const loadError = (!screen.data && screen.error) || null;

  const tabs: { id: WorkTab; label: string }[] = [
    { id: "offers", label: `Offers (${openOffers.length})` },
    { id: "active", label: `Active (${activeJobs.length})` },
    { id: "done", label: "Done" },
  ];

  return (
    <Screen glow="worker" hasTabBar>
      <h1 className="title title--page">My work</h1>

      <section className="card" aria-label="This month">
        <div className="label">{monthLabel()}</div>
        <div className="stat-grid" style={{ marginTop: 10 }}>
          <div>
            <div className="stat__value">{formatMoney(month.earned)}</div>
            <div className="stat__label">Earned</div>
          </div>
          <div>
            <div className="stat__value">{month.jobsDone}</div>
            <div className="stat__label">Jobs done</div>
          </div>
          <div>
            <div className="stat__value text-amber">
              {standing ? formatPercent(standing.on_time_rate) : "—"}
            </div>
            <div className="stat__label">On time</div>
          </div>
        </div>
      </section>

      {standing?.is_frozen && (
        <div className="banner banner--amber">
          <Icon name="shield" size={18} />
          Your standing is paused while a concern is open. Answer it from the Active tab.
        </div>
      )}

      <div className="segmented" role="tablist" aria-label="My work">
        {tabs.map((option) => (
          <button
            key={option.id}
            type="button"
            role="tab"
            aria-selected={tab === option.id}
            className="segmented__tab"
            onClick={() => setTab(option.id)}
          >
            {option.label}
          </button>
        ))}
      </div>

      {isLoading && <Skeleton height={140} count={2} />}
      {loadError && (
        <ErrorState message={loadError.message} onRetry={() => void screen.refetch()} />
      )}

      {!isLoading && tab === "offers" && (
        <>
          {openOffers.length === 0 && (
            <EmptyState
              title="No offers waiting"
              icon="send"
              action={
                <Link href="/worker" className="btn btn--primary btn--sm">
                  Find jobs
                </Link>
              }
            >
              Offers you send show here until the client decides.
            </EmptyState>
          )}
          {openOffers.map((offer) => (
            <Link key={offer.id} href={`/worker/jobs/${offer.job_id}`} className="list-row">
              <div className="grow">
                <div style={{ fontSize: 15, fontWeight: 700 }}>
                  {tradeLabel(offer.job_trade)} · {offer.job_suburb}
                </div>
                <div className="meta">
                  {offer.availability_note ?? "No time given"} · sent{" "}
                  {formatRelativeTime(offer.updated_at)}
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 16, fontWeight: 700 }}>
                  {formatMoney(offer.quoted_amount)}
                </div>
                <div className="meta" style={{ fontSize: 11 }}>
                  {jobStatusLabel(offer.job_status)}
                </div>
              </div>
            </Link>
          ))}
        </>
      )}

      {!isLoading && tab === "active" && (
        <>
          {activeJobs.length === 0 && (
            <EmptyState title="No active jobs" icon="briefcase">
              When a client hires you, the job and its address appear here.
            </EmptyState>
          )}
          {activeJobs.map((job) => (
            <ActiveJobCard key={job.id} job={job} offeredAmount={offerByJob.get(job.id) ?? null} />
          ))}
        </>
      )}

      {!isLoading && tab === "done" && (
        <>
          {doneJobs.length === 0 && (
            <EmptyState title="No finished jobs yet" icon="check">
              Each signed-off job builds your record on Maricho.
            </EmptyState>
          )}
          {doneJobs.map((job) => (
            <div key={job.id} className="list-row">
              <div className="icon-tile icon-tile--sm icon-tile--emerald">
                <Icon name="check" />
              </div>
              <div className="grow">
                <div style={{ fontSize: 14, fontWeight: 700 }} className="truncate">
                  {splitTiming(job.problem_description).text.split("\n")[0] ||
                    tradeLabel(job.trade)}
                </div>
                <div className="meta">
                  {job.suburb} · signed off {formatShortDate(job.updated_at)}
                </div>
              </div>
              <span style={{ fontWeight: 700 }}>{formatMoney(job.quote_amount)}</span>
            </div>
          ))}
        </>
      )}

      <WorkerTabBar />
    </Screen>
  );
}
