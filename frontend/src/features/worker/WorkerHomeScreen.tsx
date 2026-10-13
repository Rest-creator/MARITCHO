"use client";

import { useState } from "react";
import Link from "next/link";

import { Avatar } from "@/components/ui/Avatar";
import { Screen } from "@/components/ui/Screen";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/States";
import { Switch } from "@/components/ui/Switch";
import { firstName, greeting } from "@/core/format/format";
import { tradeWorkLabel } from "@/core/format/trades";
import { updateProfile, useLocalProfile } from "@/core/session/profile-store";
import { useMyOffers, useOpenJobs } from "@/features/jobs/hooks";
import { OpenJobCard } from "@/features/worker/OpenJobCard";
import {
  applyJobFilter,
  isSameFilter,
  jobsWithinReach,
  type JobFilter,
} from "@/features/worker/open-job-filters";
import { WorkerTabBar } from "@/features/worker/WorkerTabBar";
import { useSkills } from "@/features/workers/hooks";

/** Design W2 · Jobs near you. */
export function WorkerHomeScreen() {
  const profile = useLocalProfile();
  const skills = useSkills();
  const openJobs = useOpenJobs();
  const offers = useMyOffers();
  const [filter, setFilter] = useState<JobFilter>({ kind: "all" });

  const reachable = jobsWithinReach(openJobs.data ?? [], profile.travelKm);
  const visible = applyJobFilter(reachable, filter);
  const offeredJobIds = new Set((offers.data ?? []).map((offer) => offer.job_id));
  const hasNoSkills = skills.data !== undefined && skills.data.length === 0;
  const name = firstName(profile.name);

  const filters: { label: string; value: JobFilter }[] = [
    { label: `All (${reachable.length})`, value: { kind: "all" } },
    ...(skills.data ?? []).map((skill) => ({
      label: tradeWorkLabel(skill.trade),
      value: { kind: "trade", trade: skill.trade } as JobFilter,
    })),
    { label: "Today", value: { kind: "today" } },
  ];

  return (
    <Screen glow="worker" hasTabBar>
      <header className="topbar topbar--split">
        <div>
          <div className="meta" style={{ fontSize: 13 }}>
            {greeting()}
            {name === "" ? "" : `, ${name}`}
          </div>
          <h1 className="title title--page">Jobs near you</h1>
        </div>
        <Link href="/worker/account" aria-label="My profile">
          <Avatar name={profile.name || "Me"} seed={profile.phone} />
        </Link>
      </header>

      <div
        className={profile.isAvailable ? "banner banner--emerald" : "banner banner--quiet"}
        style={{ borderRadius: 16 }}
      >
        <span className={profile.isAvailable ? "status-dot" : "status-dot status-dot--off"} />
        <div className="grow">
          <div style={{ fontSize: 14, fontWeight: 700, color: "var(--text)" }}>
            {profile.isAvailable ? "You're available for work" : "You're taking a break"}
          </div>
          <div
            className="meta"
            style={{ color: profile.isAvailable ? "var(--emerald-pale)" : undefined }}
          >
            {profile.isAvailable
              ? `Showing jobs within ${profile.travelKm} km`
              : "Turn this on when you're ready for new jobs"}
          </div>
        </div>
        <Switch
          isOn={profile.isAvailable}
          label="Available for work"
          onToggle={(next) => updateProfile({ isAvailable: next })}
        />
      </div>

      {hasNoSkills && (
        <EmptyState
          title="Tell us what you can do"
          icon="briefcase"
          action={
            <Link href="/worker/skills" className="btn btn--primary btn--sm">
              Add your skills
            </Link>
          }
        >
          Jobs appear here once you&apos;ve picked your skills.
        </EmptyState>
      )}

      {profile.isAvailable && !hasNoSkills && (
        <>
          <div className="chip-list chip-list--scroll" role="group" aria-label="Filter jobs">
            {filters.map((option) => (
              <button
                key={option.label}
                type="button"
                className="filter-chip"
                aria-pressed={isSameFilter(filter, option.value)}
                onClick={() => setFilter(option.value)}
              >
                {option.label}
              </button>
            ))}
          </div>

          {openJobs.isPending && <Skeleton height={150} count={3} />}
          {openJobs.isError && !openJobs.data && (
            <ErrorState message={openJobs.error.message} onRetry={() => void openJobs.refetch()} />
          )}
          {openJobs.data && visible.length === 0 && (
            <EmptyState title="No jobs here right now" icon="search">
              {reachable.length === 0
                ? `Nothing within ${profile.travelKm} km yet. Travelling further shows more jobs.`
                : "Try another filter."}
            </EmptyState>
          )}
          {visible.map((job, index) => (
            <OpenJobCard
              key={job.job_id}
              job={job}
              isFeatured={index === 0}
              hasOffered={offeredJobIds.has(job.job_id)}
            />
          ))}
        </>
      )}

      <WorkerTabBar />
    </Screen>
  );
}
