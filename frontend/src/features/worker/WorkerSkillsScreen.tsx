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
import { findNearestSuburb } from "@/core/format/suburbs";
import { isUploadUnavailable } from "@/core/media/upload";
import { useMediaUploads } from "@/core/media/use-media-uploads";
import { useUpload } from "@/core/media/use-upload";
import { updateProfile, useLocalProfile } from "@/core/session/profile-store";
import { useSession } from "@/core/session/SessionProvider";
import { SkillPicker } from "@/features/worker/SkillPicker";
import {
  useRegisterServiceArea,
  useRegisterSkill,
  useServiceAreas,
  useSkills,
  useSuburbs,
  useUpdateUserProfile,
} from "@/features/workers/hooks";
import { MAX_TRAVEL_KM, MIN_TRAVEL_KM, clampTravelKm } from "@/core/format/travel";

export const MAX_SKILLS = 5;

type Props = {
  /** Same-site path to open once skills are saved (e.g. a shared job). */
  nextPath?: string | null;
};

/** Design W1 · Set up your skills. */
export function WorkerSkillsScreen({ nextPath = null }: Props) {
  const router = useRouter();
  const profile = useLocalProfile();
  const { user } = useSession();
  const skills = useSkills();
  const serviceAreas = useServiceAreas();
  const suburbs = useSuburbs();
  const registerSkill = useRegisterSkill();
  const registerArea = useRegisterServiceArea();
  const updateServerProfile = useUpdateUserProfile();
  const canUpload = useMediaUploads();
  const { upload } = useUpload();

  const registered = new Set<Trade>((skills.data ?? []).map((skill) => skill.trade));
  const [picked, setPicked] = useState<Trade[]>([]);
  const [photos, setPhotos] = useState<File[]>([]);
  // The account's saved distance wins over this phone's copy, which may be stale
  // (e.g. set on another device). Only an edit here overrides it.
  const [travelDraft, setTravelDraft] = useState<number | null>(null);
  const travelKm: number = clampTravelKm(travelDraft ?? user?.travel_km ?? profile.travelKm);
  const [chosenSuburb, setSuburb] = useState("");
  const [isLocatingSuburb, setIsLocatingSuburb] = useState(false);
  const [locationNote, setLocationNote] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const isFirstSetup = skills.data !== undefined && skills.data.length === 0;
  const total = registered.size + picked.length;
  const suburb = chosenSuburb || serviceAreas.data?.[0]?.suburb || profile.homeSuburb;
  const knownArea = (serviceAreas.data ?? []).some((area) => area.suburb === suburb);

  function handleUseCurrentLocation(): void {
    if (typeof navigator === "undefined" || !("geolocation" in navigator)) {
      setLocationNote("Location isn't available on this device. Choose your suburb from the list.");
      return;
    }
    setIsLocatingSuburb(true);
    setLocationNote(null);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const nearest = findNearestSuburb(
          position.coords.latitude,
          position.coords.longitude,
          suburbs.data,
        );
        setSuburb(nearest.suburb);
        setIsLocatingSuburb(false);
        setLocationNote(`Detected nearest suburb: ${nearest.suburb} (${nearest.distanceKm} km).`);
      },
      () => {
        setIsLocatingSuburb(false);
        setLocationNote("Could not get your location. Choose your suburb from the list.");
      },
      { enableHighAccuracy: true, timeout: 10_000, maximumAge: 60_000 },
    );
  }

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
    // How they travel was asked at sign-up; it rides along with the first area.
    const serviceArea = {
      suburb,
      ...(profile.travelMeans === "" ? {} : { travel_means: profile.travelMeans }),
    };
    updateProfile({ travelKm, homeSuburb: suburb });
    updateServerProfile.mutate({ travel_km: travelKm, home_suburb: suburb });
    if (!onlineManager.isOnline()) {
      // Queue everything; it sends itself when the connection returns.
      picked.forEach((trade) => registerSkill.mutate(trade));
      if (!knownArea) registerArea.mutate(serviceArea);
      setIsSaving(false);
      router.replace(nextPath ?? "/worker");
      return;
    }
    try {
      let proofUrl: string | undefined;
      if (photos[0] !== undefined && canUpload) {
        try {
          proofUrl = await upload(photos[0], "photo");
        } catch (failure: unknown) {
          if (!isUploadUnavailable(failure)) throw failure;
        }
      }
      // Sequential on purpose: one small request at a time on a weak connection.
      for (const trade of picked) {
        await registerSkill.mutateAsync(proofUrl ? { trade, proof_url: proofUrl } : trade);
      }
      if (!knownArea) {
        await registerArea.mutateAsync(serviceArea);
      }
      router.replace(nextPath ?? "/worker");
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

      <SkillPicker registered={registered} picked={picked} max={MAX_SKILLS} onToggle={toggle} />

      <section className="card" style={{ padding: 14 }}>
        <div style={{ fontSize: 15, fontWeight: 700 }}>Show your work</div>
        <div className="meta meta--secondary" style={{ marginTop: 3, lineHeight: 1.5 }}>
          Photos of jobs you&apos;ve done. Clients trust what they can see.
        </div>
        <div style={{ marginTop: 12 }}>
          <PhotoStrip layout="grid" max={6} addLabel="Add" onChange={setPhotos} />
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
          min={MIN_TRAVEL_KM}
          max={MAX_TRAVEL_KM}
          value={travelKm}
          aria-valuetext={`${travelKm} kilometres`}
          onChange={(event) => setTravelDraft(clampTravelKm(Number(event.target.value)))}
          style={{ marginTop: 12 }}
        />
        <div className="row row--between row--baseline" style={{ marginTop: 12 }}>
          <label htmlFor="ws-suburb" className="field__label">
            From
          </label>
          <button
            type="button"
            className="text-link row row--tight"
            style={{ fontSize: 13 }}
            disabled={isLocatingSuburb}
            onClick={handleUseCurrentLocation}
          >
            <Icon name="pin" size={14} />
            {isLocatingSuburb ? "Finding location…" : "Use my location"}
          </button>
        </div>
        <select
          id="ws-suburb"
          className="input"
          style={{ marginTop: 8, height: 48 }}
          value={suburb}
          onChange={(event) => {
            setSuburb(event.target.value);
            setLocationNote(null);
          }}
        >
          <option value="">{suburbs.isPending ? "Loading suburbs…" : "Choose your suburb"}</option>
          {(suburbs.data ?? []).map((item) => (
            <option key={item.name} value={item.name}>
              {item.name}
            </option>
          ))}
        </select>
        {locationNote && (
          <p className="meta text-emerald" style={{ marginTop: 6 }} role="status">
            {locationNote}
          </p>
        )}
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
