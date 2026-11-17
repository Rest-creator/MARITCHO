"use client";

import { useState, type KeyboardEvent } from "react";
import Link from "next/link";

import { Avatar } from "@/components/ui/Avatar";
import { Icon } from "@/components/ui/Icon";
import { Screen } from "@/components/ui/Screen";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/States";
import type { Trade, WorkerSummary } from "@/core/api/schemas";
import {
  distanceBandLabel,
  formatKm,
  formatPercent,
  gradeLabel,
  isVerifiedGrade,
} from "@/core/format/format";
import { matchSuburbs, mergeSuburbs, predictSuburb } from "@/core/format/suburbs";
import { tradeIcon, tradeLabel, TRADES } from "@/core/format/trades";
import { useDebouncedValue } from "@/core/hooks/useDebouncedValue";
import { updateProfile, useLocalProfile } from "@/core/session/profile-store";
import { EmployerTabBar } from "@/features/employer/EmployerTabBar";
import { candidateTitle } from "@/features/jobs/job-helpers";
import { useNearbyWorkers, useSuburbs } from "@/features/workers/hooks";

function workerTitle(worker: WorkerSummary): string {
  const primaryTrade = worker.trades[0] ?? "BUILDING";
  return candidateTitle({ grade: worker.grade, display_name: worker.display_name }, primaryTrade);
}

/** Employer directory: browse workers close to where you are and open their profiles. */
export function WorkersScreen() {
  const profile = useLocalProfile();
  const suburbs = useSuburbs();
  const allSuburbs = mergeSuburbs(suburbs.data);

  const initialSuburb = profile.lastSuburb || profile.homeSuburb || "Hillside";
  const [suburbInput, setSuburbInput] = useState(initialSuburb);
  const [isSuburbMenuOpen, setIsSuburbMenuOpen] = useState(false);
  const [isFilteringSuburb, setIsFilteringSuburb] = useState(false);
  const [activeSuburbIndex, setActiveSuburbIndex] = useState(0);
  const [selectedTrade, setSelectedTrade] = useState<Trade | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const debouncedQuery = useDebouncedValue(searchQuery, 200);
  const debouncedSuburb = useDebouncedValue(suburbInput, 200);

  const canonicalSuburb =
    allSuburbs.find((item) => item.toLowerCase() === debouncedSuburb.trim().toLowerCase()) ??
    debouncedSuburb.trim();

  const workers = useNearbyWorkers({
    ...(canonicalSuburb === "" ? {} : { suburb: canonicalSuburb }),
    ...(selectedTrade === null ? {} : { trade: selectedTrade }),
    ...(debouncedQuery.trim() === "" ? {} : { q: debouncedQuery.trim() }),
  });

  const suburbMatches = matchSuburbs(isFilteringSuburb ? suburbInput : "", allSuburbs);
  const suburbPrediction =
    suburbInput.trim() !== "" ? predictSuburb(suburbInput, allSuburbs) : null;

  function pickSuburb(name: string): void {
    setSuburbInput(name);
    updateProfile({ lastSuburb: name });
    setIsFilteringSuburb(false);
    setIsSuburbMenuOpen(false);
    setActiveSuburbIndex(0);
  }

  function handleSuburbKeyDown(event: KeyboardEvent<HTMLInputElement>): void {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setIsSuburbMenuOpen(true);
      if (suburbMatches.length > 0) {
        setActiveSuburbIndex((current) => (current + 1) % suburbMatches.length);
      }
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      setIsSuburbMenuOpen(true);
      if (suburbMatches.length > 0) {
        setActiveSuburbIndex(
          (current) => (current - 1 + suburbMatches.length) % suburbMatches.length,
        );
      }
      return;
    }
    if (
      (event.key === "Enter" || event.key === "Tab") &&
      isSuburbMenuOpen &&
      suburbInput.trim() !== ""
    ) {
      const target = suburbMatches[activeSuburbIndex] ?? suburbPrediction;
      if (target !== undefined && target !== null && target !== suburbInput) {
        event.preventDefault();
        pickSuburb(target);
      }
    }
  }

  return (
    <Screen hasTabBar>
      <div className="topbar topbar--split">
        <div className="topbar__text">
          <div className="eyebrow">People near you</div>
          <h1 className="title title--page" style={{ marginTop: 2 }}>
            Workers near you
          </h1>
        </div>
        <Link href="/employer/post?pick=1" className="btn btn--primary btn--sm">
          <Icon name="plus" size={16} strokeWidth={2.2} />
          Post a job
        </Link>
      </div>

      <section className="card card--compact stack" style={{ gap: 10 }} aria-label="Filter workers">
        <div className="field" style={{ gap: 6 }}>
          <label htmlFor="wk-suburb" className="field__label">
            Close to which suburb?
          </label>
          <div className="combobox">
            <div className="combobox__control">
              <input
                id="wk-suburb"
                type="text"
                role="combobox"
                aria-expanded={isSuburbMenuOpen}
                aria-autocomplete="list"
                aria-controls="wk-suburb-listbox"
                className="input input--compact combobox__input"
                placeholder="Choose or write in your suburb"
                value={suburbInput}
                maxLength={100}
                onFocus={() => {
                  setIsSuburbMenuOpen(true);
                  setIsFilteringSuburb(false);
                }}
                onChange={(event) => {
                  setSuburbInput(event.target.value);
                  setIsFilteringSuburb(true);
                  setIsSuburbMenuOpen(true);
                  setActiveSuburbIndex(0);
                }}
                onKeyDown={handleSuburbKeyDown}
              />
              {suburbPrediction !== null &&
                suburbPrediction.toLowerCase() !== suburbInput.trim().toLowerCase() && (
                  <button
                    type="button"
                    className="combobox__autofill"
                    onClick={() => pickSuburb(suburbPrediction)}
                  >
                    {suburbPrediction}
                  </button>
                )}
              <button
                type="button"
                className="combobox__toggle"
                aria-label={isSuburbMenuOpen ? "Hide suburb options" : "Show suburb options"}
                onClick={() => {
                  setIsFilteringSuburb(false);
                  setIsSuburbMenuOpen((open) => !open);
                }}
              >
                <Icon name="chevronDown" size={18} />
              </button>
            </div>
            {isSuburbMenuOpen && suburbMatches.length > 0 && (
              <ul
                id="wk-suburb-listbox"
                role="listbox"
                aria-label="Suburb options"
                className="combobox__menu"
              >
                {suburbMatches.map((name, index) => {
                  const isSelected = name.toLowerCase() === suburbInput.trim().toLowerCase();
                  const isClosest =
                    isFilteringSuburb && suburbInput.trim() !== "" && index === activeSuburbIndex;
                  return (
                    <li key={name} role="option" aria-selected={isSelected || isClosest}>
                      <button
                        type="button"
                        className={
                          isSelected || isClosest
                            ? "combobox__option combobox__option--active"
                            : "combobox__option"
                        }
                        onClick={() => pickSuburb(name)}
                      >
                        <span>{name}</span>
                        {isSelected ? (
                          <span className="combobox__badge">Selected</span>
                        ) : isClosest ? (
                          <span className="combobox__badge">Closest match</span>
                        ) : null}
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </div>

        <label className="search" style={{ height: 46 }}>
          <Icon name="search" />
          <input
            type="search"
            placeholder="Search by worker name, trade, or skill…"
            aria-label="Search workers"
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
          />
        </label>

        <div className="chip-list chip-list--scroll" role="group" aria-label="Filter by trade">
          <button
            type="button"
            className="filter-chip"
            aria-pressed={selectedTrade === null}
            onClick={() => setSelectedTrade(null)}
          >
            All trades
          </button>
          {TRADES.map((trade) => (
            <button
              key={trade}
              type="button"
              className="filter-chip"
              aria-pressed={selectedTrade === trade}
              onClick={() => setSelectedTrade(selectedTrade === trade ? null : trade)}
            >
              {tradeLabel(trade)}
            </button>
          ))}
        </div>
      </section>

      {workers.isPending && <Skeleton height={136} count={3} />}
      {workers.isError && !workers.data && (
        <ErrorState message={workers.error.message} onRetry={() => void workers.refetch()} />
      )}
      {workers.data && workers.data.length === 0 && (
        <EmptyState title="No workers match right now" icon="users">
          Try clearing the filter or post a job so nearby workers can send you an offer.
        </EmptyState>
      )}

      {workers.data && workers.data.length > 0 && (
        <div className="cards-grid stack" style={{ gap: 12 }}>
          {workers.data.map((worker) => {
            const title = workerTitle(worker);
            const primaryTrade = worker.trades[0] ?? "BUILDING";
            const hasHistory = worker.jobs_completed > 0;
            const profileHref = `/employer/workers/${encodeURIComponent(worker.worker_id)}${
              canonicalSuburb ? `?suburb=${encodeURIComponent(canonicalSuburb)}` : ""
            }`;
            return (
              <article key={worker.worker_id} className="card stack" style={{ gap: 12 }}>
                <div className="row" style={{ gap: 12, alignItems: "flex-start" }}>
                  <Avatar name={title} seed={worker.worker_id} isOnline={worker.is_available} />
                  <div className="grow">
                    <div className="row row--between" style={{ gap: 8 }}>
                      <div className="row row--tight">
                        <span style={{ fontSize: 16, fontWeight: 700 }}>{title}</span>
                        {isVerifiedGrade(worker.grade) && (
                          <span className="text-emerald" style={{ display: "inline-flex" }}>
                            <Icon name="shieldCheck" size={16} label="Checked by Maricho" />
                          </span>
                        )}
                      </div>
                      {worker.distance_band && (
                        <span className="badge badge--emerald">
                          {distanceBandLabel(worker.distance_band)}
                          {worker.distance_km !== null && worker.distance_km !== undefined
                            ? ` · ${formatKm(worker.distance_km)}`
                            : ""}
                        </span>
                      )}
                    </div>
                    <div className="meta meta--secondary" style={{ marginTop: 2 }}>
                      {gradeLabel(worker.grade)} · {worker.suburb ?? "Bulawayo"}
                      {worker.rating_average !== null && worker.rating_average !== undefined
                        ? ` · ★ ${worker.rating_average.toFixed(1)} (${worker.rating_count ?? 0})`
                        : ""}
                    </div>
                  </div>
                </div>

                <div className="chip-list" style={{ gap: 6 }}>
                  {typeof worker.similarity_score === "number" &&
                    worker.similarity_score >= 0.35 && (
                      <span className="tag tag--verified">
                        <Icon name="check" size={12} strokeWidth={2.4} />
                        Strong match
                      </span>
                    )}
                  {worker.trades.map((trade) => (
                    <span key={trade} className="tag">
                      <Icon name={tradeIcon(trade)} size={13} />
                      {tradeLabel(trade)}
                    </span>
                  ))}
                  <span className="tag">
                    {hasHistory
                      ? `${formatPercent(worker.on_time_rate)} on time`
                      : "New on Maricho"}
                  </span>
                  <span className="tag">{worker.jobs_completed} jobs done</span>
                </div>

                <div className="btn-grid">
                  <Link href={profileHref} className="btn">
                    View profile
                  </Link>
                  <Link href={`/employer/post?trade=${primaryTrade}`} className="btn btn--soft">
                    Hire for {tradeLabel(primaryTrade).toLowerCase()}
                  </Link>
                </div>
              </article>
            );
          })}
        </div>
      )}
      <EmployerTabBar />
    </Screen>
  );
}
