"use client";

import Link from "next/link";

import { Icon, type IconName } from "@/components/ui/Icon";
import { Screen } from "@/components/ui/Screen";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/States";
import type { Trade } from "@/core/api/schemas";
import { firstName, greeting } from "@/core/format/format";
import { useLocalProfile } from "@/core/session/profile-store";
import { EmployerJobCard } from "@/features/employer/EmployerJobCard";
import { EmployerTabBar } from "@/features/employer/EmployerTabBar";
import { activeJobs, finishedJobs } from "@/features/jobs/job-helpers";
import { useMyJobs } from "@/features/jobs/hooks";

interface PopularTrade {
  trade: Trade;
  label: string;
  icon: IconName;
  tone: "amber" | "emerald";
}

const POPULAR: readonly PopularTrade[] = [
  { trade: "PLUMBING", label: "Plumber", icon: "drop", tone: "amber" },
  { trade: "ELECTRICAL", label: "Electrician", icon: "bolt", tone: "amber" },
  { trade: "SOLAR", label: "Solar", icon: "sun", tone: "amber" },
  { trade: "BUILDING", label: "Builder", icon: "bricks", tone: "amber" },
  { trade: "WELDING", label: "Welder", icon: "flame", tone: "emerald" },
  { trade: "APPLIANCE_REPAIR", label: "Appliances", icon: "appliance", tone: "emerald" },
];

/** Design E1 · Employer home. */
export function EmployerHomeScreen() {
  const profile = useLocalProfile();
  const jobs = useMyJobs();
  const active = activeJobs(jobs.data ?? []);
  const recentDone = finishedJobs(jobs.data ?? []).slice(0, 2);
  const hasNewOffers = active.some((job) => job.offer_count > 0 && job.status !== "BOOKED");
  const name = firstName(profile.name);

  return (
    <Screen hasTabBar bodyClassName="screen__body--roomy screen__body--fab">
      <header className="topbar topbar--split">
        <div>
          <div className="meta" style={{ fontSize: 13 }}>
            {greeting()}
          </div>
          <h1 className="title title--page">{name === "" ? "Welcome" : name}</h1>
        </div>
        <Link
          href="/employer/jobs"
          className="icon-btn"
          aria-label={hasNewOffers ? "New offers on your jobs" : "Your jobs"}
        >
          <Icon name="bell" strokeWidth={1.8} />
          {hasNewOffers && <span className="icon-btn__dot" />}
        </Link>
      </header>

      <Link href="/employer/post" className="card row" style={{ gap: 14, padding: 18 }}>
        <span className="text-amber" style={{ display: "flex" }}>
          <Icon name="search" size={22} />
        </span>
        <div className="grow">
          <div style={{ fontSize: 17, fontWeight: 700 }}>What needs doing?</div>
          <div className="meta meta--secondary" style={{ marginTop: 2, fontSize: 13 }}>
            A leaking tap, a broken gate, a solar fault…
          </div>
        </div>
      </Link>

      <section aria-labelledby="popular-heading">
        <div className="row row--between row--baseline">
          <h2 id="popular-heading" className="section-title">
            Popular near you
          </h2>
          <Link href="/employer/post?pick=1" className="text-link">
            All skills
          </Link>
        </div>
        <div
          className="trade-grid"
          style={{ marginTop: 12, gridTemplateColumns: "repeat(3, minmax(0, 1fr))" }}
        >
          {POPULAR.map((item) => (
            <Link
              key={item.trade}
              href={`/employer/post?trade=${item.trade}`}
              className={`trade-tile trade-tile--${item.tone}`}
            >
              <Icon name={item.icon} size={22} strokeWidth={1.75} />
              <span>{item.label}</span>
            </Link>
          ))}
        </div>
      </section>

      <section aria-labelledby="jobs-heading">
        <h2 id="jobs-heading" className="section-title">
          Your jobs
        </h2>
        <div className="stack" style={{ marginTop: 12 }}>
          {jobs.isPending && <Skeleton height={110} count={2} />}
          {jobs.isError && !jobs.data && (
            <ErrorState message={jobs.error.message} onRetry={() => void jobs.refetch()} />
          )}
          {jobs.data && active.length === 0 && recentDone.length === 0 && (
            <EmptyState title="No jobs yet" icon="briefcase">
              Post what needs doing — checked workers nearby will offer to help.
            </EmptyState>
          )}
          {active.slice(0, 3).map((job) => (
            <EmployerJobCard key={job.id} job={job} />
          ))}
          {recentDone.map((job) => (
            <EmployerJobCard key={job.id} job={job} />
          ))}
        </div>
      </section>

      <Link href="/employer/post" className="fab">
        <Icon name="plus" strokeWidth={2.2} />
        Post a job
      </Link>
      <EmployerTabBar />
    </Screen>
  );
}
