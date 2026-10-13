"use client";

import { useState } from "react";
import { onlineManager } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { BackButton } from "@/components/ui/BackButton";
import { Icon } from "@/components/ui/Icon";
import { PhotoStrip } from "@/components/ui/PhotoStrip";
import { Screen } from "@/components/ui/Screen";
import { ErrorState } from "@/components/ui/States";
import type { Trade } from "@/core/api/schemas";
import { ALL_SKILLS, searchSkills, tradeLabel } from "@/core/format/trades";
import { updateProfile, useLocalProfile } from "@/core/session/profile-store";
import {
  useRegisterServiceArea,
  useRegisterSkill,
  useServiceAreas,
  useSkills,
  useSuburbs,
} from "@/features/workers/hooks";

export const MAX_SKILLS = 5;

/** One chip per backend trade, labelled the way workers describe themselves. */
const TRADE_CHIPS = ALL_SKILLS.filter(
  (skill) => skill.trade !== null && skill.label === tradeLabel(skill.trade),
);
const SOON_CHIPS = ALL_SKILLS.filter((skill) => skill.trade === null);

/** Design W1 · Set up your skills. */
export function WorkerSkillsScreen() {
  const router = useRouter();
  const profile = useLocalProfile();
  const skills = useSkills();
  const serviceAreas = useServiceAreas();
  const suburbs = useSuburbs();
  const registerSkill = useRegisterSkill();
  const registerArea = useRegisterServiceArea();

  const registered = new Set<Trade>((skills.data ?? []).map((skill) => skill.trade));
  const [picked, setPicked] = useState<Trade[]>([]);
  const [query, setQuery] = useState("");
  const [travelKm, setTravelKm] = useState(profile.travelKm);
  const [chosenSuburb, setSuburb] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const isFirstSetup = skills.data !== undefined && skills.data.length === 0;
  const total = registered.size + picked.length;
  const matchingIds = new Set(
    searchSkills(query).flatMap((group) => group.skills.map((s) => s.id)),
  );
  const suburb = chosenSuburb || serviceAreas.data?.[0]?.suburb || profile.homeSuburb;
  const knownArea = (serviceAreas.data ?? []).some((area) => area.suburb === suburb);

  function toggle(trade: Trade): void {
    if (registered.has(trade)) return;
    setPicked((current) =>
      current.includes(trade)
        ? current.filter((item) => item !== trade)
        : total >= MAX_SKILLS
          ? current
          : [...current, trade],
    );
  }

  async function handleSave(): Promise<void> {
    if (total === 0) {
      setError("Pick at least one kind of work you can do.");
      return;
    }
    if (suburb === "") {
      setError("Choose where you're based so we can show jobs nearby.");
      return;
    }
    setError(null);
    setIsSaving(true);
    updateProfile({ travelKm, homeSuburb: suburb });
    if (!onlineManager.isOnline()) {
      // Queue everything; it sends itself when the connection returns.
      picked.forEach((trade) => registerSkill.mutate(trade));
      if (!knownArea) registerArea.mutate({ suburb });
      setIsSaving(false);
      router.replace("/worker");
      return;
    }
    try {
      // Sequential on purpose: one small request at a time on a weak connection.
      for (const trade of picked) {
        await registerSkill.mutateAsync(trade);
      }
      if (!knownArea) {
        await registerArea.mutateAsync({ suburb });
      }
      router.replace("/worker");
    } catch (failure: unknown) {
      setError(failure instanceof Error ? failure.message : "Could not save. Please try again.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <Screen glow="worker">
      <div className="topbar topbar--split">
        <BackButton fallbackHref={isFirstSetup ? "/signup" : "/worker/account"} />
        {isFirstSetup && (
          <div className="label" style={{ fontSize: 13 }}>
            Step 2 of 2
          </div>
        )}
      </div>
      {isFirstSetup && (
        <div className="progress">
          <div className="progress__fill progress__fill--emerald" style={{ width: "100%" }} />
        </div>
      )}
      <div>
        <h1 className="title" style={{ marginTop: 6, fontSize: 26, letterSpacing: "-0.02em" }}>
          What work can you do?
        </h1>
        <p
          className="meta meta--secondary"
          style={{ marginTop: 8, fontSize: 14, lineHeight: 1.55 }}
        >
          Pick up to {MAX_SKILLS}. Here, what you can do matters more than certificates.
        </p>
      </div>

      {skills.isError && !skills.data && (
        <ErrorState message={skills.error.message} onRetry={() => void skills.refetch()} />
      )}

      <label className="search" style={{ height: 48 }}>
        <Icon name="search" />
        <input
          type="search"
          placeholder="Search skills"
          aria-label="Search skills"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
      </label>

      <div className="chip-list" role="group" aria-label="Your skills">
        {TRADE_CHIPS.filter((skill) => matchingIds.has(skill.id)).map((skill) => {
          const trade = skill.trade as Trade;
          const isOn = registered.has(trade) || picked.includes(trade);
          return (
            <button
              key={skill.id}
              type="button"
              className="chip chip--emerald"
              aria-pressed={isOn}
              disabled={registered.has(trade)}
              style={registered.has(trade) ? { opacity: 1 } : undefined}
              onClick={() => toggle(trade)}
            >
              {isOn && <Icon name="check" size={16} strokeWidth={2.4} />}
              {skill.label}
            </button>
          );
        })}
        {SOON_CHIPS.filter((skill) => matchingIds.has(skill.id))
          .slice(0, query === "" ? 4 : undefined)
          .map((skill) => (
            <button key={skill.id} type="button" className="chip" disabled>
              {skill.label}
              <span className="chip__soon">SOON</span>
            </button>
          ))}
      </div>

      <section className="card" style={{ padding: 14 }}>
        <div style={{ fontSize: 15, fontWeight: 700 }}>Show your work</div>
        <div className="meta meta--secondary" style={{ marginTop: 3, lineHeight: 1.5 }}>
          Photos of jobs you&apos;ve done. Clients trust what they can see.
        </div>
        <div style={{ marginTop: 12 }}>
          <PhotoStrip layout="grid" max={6} addLabel="Add" />
        </div>
      </section>

      <section className="card" style={{ padding: 14 }}>
        <div className="row row--between row--baseline">
          <label htmlFor="ws-range" style={{ fontSize: 15, fontWeight: 700 }}>
            How far can you travel?
          </label>
          <span className="text-emerald" style={{ fontSize: 15, fontWeight: 700 }}>
            {travelKm} km
          </span>
        </div>
        <input
          id="ws-range"
          className="range"
          type="range"
          min={1}
          max={25}
          value={travelKm}
          aria-valuetext={`${travelKm} kilometres`}
          onChange={(event) => setTravelKm(Number(event.target.value))}
          style={{ marginTop: 12 }}
        />
        <label
          htmlFor="ws-suburb"
          className="field__label"
          style={{ display: "block", marginTop: 12 }}
        >
          From
        </label>
        <select
          id="ws-suburb"
          className="input"
          style={{ marginTop: 8, height: 48 }}
          value={suburb}
          onChange={(event) => setSuburb(event.target.value)}
        >
          <option value="">{suburbs.isPending ? "Loading suburbs…" : "Choose your suburb"}</option>
          {(suburbs.data ?? []).map((item) => (
            <option key={item.name} value={item.name}>
              {item.name}
            </option>
          ))}
        </select>
      </section>

      {error && (
        <p className="field-error" role="alert">
          {error}
        </p>
      )}
      <div className="spacer" />
      <button
        type="button"
        className="btn btn--primary btn--cta"
        disabled={isSaving}
        onClick={() => void handleSave()}
      >
        {isSaving ? "Saving…" : isFirstSetup ? "Start finding work" : "Save"}
        {!isSaving && <Icon name="arrowRight" size={18} strokeWidth={2.2} />}
      </button>
    </Screen>
  );
}
