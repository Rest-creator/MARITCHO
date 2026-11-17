"use client";

import { useId, useMemo, useState, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { Avatar } from "@/components/ui/Avatar";
import { Celebration } from "@/components/ui/Celebration";
import { Icon } from "@/components/ui/Icon";
import { PhotoPicker } from "@/components/ui/PhotoPicker";
import { Screen } from "@/components/ui/Screen";
import { Switch } from "@/components/ui/Switch";
import type { Grade } from "@/core/api/schemas";
import {
  formatLocalPhone,
  formatMoney,
  formatPercent,
  formatShortDate,
  gradeLabel,
  isVerifiedGrade,
  toInternationalPhone,
} from "@/core/format/format";
import { matchSuburbs, mergeSuburbs } from "@/core/format/suburbs";
import { tradeIcon, tradeLabel } from "@/core/format/trades";
import { isUploadUnavailable } from "@/core/media/upload";
import { useMediaUploads } from "@/core/media/use-media-uploads";
import { useUpload } from "@/core/media/use-upload";
import { queryKeys } from "@/core/query/keys";
import { updateProfile, useLocalProfile } from "@/core/session/profile-store";
import { homeFor, useSession, type SignInRole } from "@/core/session/SessionProvider";
import { activeJobs, finishedJobs } from "@/features/jobs/job-helpers";
import { useAssignedJobs, useMyJobs, useMyOffers } from "@/features/jobs/hooks";
import { monthLabel, summariseMonth } from "@/features/worker/earnings";
import {
  useAddReference,
  useReferences,
  useRegisterServiceArea,
  useServiceAreas,
  useSkills,
  useStanding,
  useSubmitIdPhoto,
  useSuburbs,
  useUpdateUserProfile,
  useVouchForWorker,
  useWorkerVetting,
} from "@/features/workers/hooks";
import {
  MAX_TRAVEL_KM,
  MIN_TRAVEL_KM,
  TRAVEL_MEANS_OPTIONS,
  clampTravelKm,
} from "@/core/format/travel";

type Props = { tabBar: ReactNode };

const GRADE_TIERS: readonly {
  grade: Grade;
  shortLabel: string;
  requirement: string;
}[] = [
  { grade: "REGISTERED", shortLabel: "Registered", requirement: "Account created" },
  { grade: "IDENTIFIED", shortLabel: "ID checked", requirement: "National ID photo submitted" },
  { grade: "APPRENTICE", shortLabel: "Apprentice", requirement: "ID + 1 contactable reference" },
  { grade: "JOURNEYMAN", shortLabel: "Journeyman", requirement: "1 Journeyman+ peer vouch" },
  { grade: "EXPERT", shortLabel: "Expert", requirement: "3 Journeyman+ peer vouches" },
];

const GRADE_ORDER: Record<Grade, number> = {
  REGISTERED: 0,
  IDENTIFIED: 1,
  APPRENTICE: 2,
  JOURNEYMAN: 3,
  EXPERT: 4,
};

export function AccountScreen({ tabBar }: Props) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user, signOut } = useSession();
  const profile = useLocalProfile();
  const updateServerProfile = useUpdateUserProfile();
  const suburbsQuery = useSuburbs();

  const isWorker = user?.role === "WORKER";
  const displayName = profile.name || user?.display_name || "Your account";
  const displayPhone = formatLocalPhone(user?.phone ?? profile.phone);

  // Worker-only queries (gated by role to avoid 403s for employers)
  const standing = useStanding(isWorker);
  const vetting = useWorkerVetting(isWorker);
  const references = useReferences(isWorker);
  const skills = useSkills(isWorker);
  const serviceAreas = useServiceAreas(isWorker);
  const assignedJobs = useAssignedJobs();
  const myOffers = useMyOffers();

  // Employer-only queries
  const employerJobs = useMyJobs();

  // Worker mutations
  const registerServiceArea = useRegisterServiceArea();
  const submitIdPhoto = useSubmitIdPhoto();
  const addReference = useAddReference();
  const vouchForWorker = useVouchForWorker();
  const canUpload = useMediaUploads();
  const { upload, isUploading: isUploadingMedia } = useUpload();

  // Personal & emergency profile state
  const [nameDraft, setNameDraft] = useState<string | null>(null);
  const name = nameDraft ?? (profile.name || user?.display_name || "");
  const [nextOfKinPhoneDraft, setNextOfKinPhoneDraft] = useState<string | null>(null);
  const nextOfKinPhone =
    nextOfKinPhoneDraft ?? formatLocalPhone(user?.next_of_kin_phone ?? profile.nextOfKinPhone);
  const [bio, setBio] = useState(profile.bio);
  const [profileFeedback, setProfileFeedback] = useState<string | null>(null);

  // Suburb & reach / location defaults state
  const initialSuburb =
    user?.home_suburb ||
    profile.homeSuburb ||
    serviceAreas.data?.[0]?.suburb ||
    profile.lastSuburb ||
    "";
  const [suburbOverride, setSuburbOverride] = useState<string | null>(null);
  const suburbDraft = suburbOverride ?? initialSuburb;
  const [isSuburbOpen, setIsSuburbOpen] = useState(false);
  const [travelDraft, setTravelDraft] = useState<number | null>(null);
  const travelKm: number = clampTravelKm(travelDraft ?? user?.travel_km ?? profile.travelKm);
  const [travelMeans, setTravelMeans] = useState(
    serviceAreas.data?.[0]?.travel_means || profile.travelMeans || "Kombi / bus",
  );
  const [defaultAddress, setDefaultAddress] = useState(profile.lastAddress);
  const [defaultLandmark, setDefaultLandmark] = useState(profile.defaultLandmark);
  const [preferredCurrency, setPreferredCurrency] = useState<"USD" | "ECOCASH" | "ZWG">(
    profile.preferredCurrency,
  );
  const [locationFeedback, setLocationFeedback] = useState<string | null>(null);

  // Vetting & references state (Worker)
  const [isIdPickerOpen, setIsIdPickerOpen] = useState(false);
  const [refName, setRefName] = useState("");
  const [refPhone, setRefPhone] = useState("");
  const [vouchWorkerId, setVouchWorkerId] = useState("");
  const [vettingFeedback, setVettingFeedback] = useState<string | null>(null);
  const [vettingError, setVettingError] = useState<string | null>(null);
  const [copiedWorkerId, setCopiedWorkerId] = useState(false);
  const [isSwitchingRole, setIsSwitchingRole] = useState(false);

  const suburbListboxId = useId();

  const availableSuburbs = useMemo(() => mergeSuburbs(suburbsQuery.data), [suburbsQuery.data]);

  const predictedSuburbs = useMemo(
    () => matchSuburbs(suburbDraft, availableSuburbs).slice(0, 8),
    [suburbDraft, availableSuburbs],
  );

  // Worker computed metrics
  const currentGrade: Grade = vetting.data?.grade ?? standing.data?.grade ?? "REGISTERED";
  const currentGradeRank = GRADE_ORDER[currentGrade];
  const hasWorkerHistory = (standing.data?.jobs_completed ?? 0) > 0;
  const workerMonthSummary = useMemo(
    () => summariseMonth(assignedJobs.data ?? []),
    [assignedJobs.data],
  );
  const workerTotalEarned = useMemo(
    () =>
      (assignedJobs.data ?? [])
        .filter((job) => job.status === "COMPLETED")
        .reduce((sum, job) => sum + (job.quote_amount ?? 0), 0),
    [assignedJobs.data],
  );
  const workerActiveAssignedCount = useMemo(
    () =>
      (assignedJobs.data ?? []).filter(
        (job) =>
          job.status === "BOOKED" || job.status === "IN_PROGRESS" || job.status === "DISPUTED",
      ).length,
    [assignedJobs.data],
  );
  const referenceList = references.data ?? [];
  const referenceCount = Math.max(referenceList.length, vetting.data?.reference_count ?? 0);
  const vouchCount = vetting.data?.vouch_count ?? 0;
  const hasIdVerified = Boolean(vetting.data?.id_photo_url) || currentGradeRank >= 1;
  const canVouchForPeers = currentGrade === "JOURNEYMAN" || currentGrade === "EXPERT";
  // Only once the server has confirmed the tier, and only for a tier this phone hasn't celebrated.
  const gradeToCelebrate: Grade | null =
    isWorker && vetting.isSuccess && currentGradeRank > GRADE_ORDER[profile.celebratedGrade]
      ? currentGrade
      : null;

  // Employer computed metrics
  const employerActiveList = useMemo(
    () => activeJobs(employerJobs.data ?? []),
    [employerJobs.data],
  );
  const employerDoneList = useMemo(
    () => finishedJobs(employerJobs.data ?? []),
    [employerJobs.data],
  );
  const employerWaitingOffers = useMemo(
    () =>
      employerActiveList.reduce(
        (sum, job) =>
          sum + (job.status === "REQUESTED" || job.status === "MATCHED" ? job.offer_count : 0),
        0,
      ),
    [employerActiveList],
  );
  const employerTotalSpent = useMemo(
    () =>
      employerDoneList.reduce((sum, job) => sum + (job.quote_amount ?? job.budget_amount ?? 0), 0),
    [employerDoneList],
  );

  async function handleRoleSwitch(targetRole: SignInRole): Promise<void> {
    if (!user || user.role === targetRole || isSwitchingRole) return;
    setIsSwitchingRole(true);
    try {
      const updated = await updateServerProfile.mutateAsync({ role: targetRole });
      queryClient.setQueryData(queryKeys.session, updated);
      router.replace(homeFor(targetRole));
    } catch {
      setIsSwitchingRole(false);
    }
  }

  function handleSavePersonalDetails(event: React.FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const trimmedName = name.trim();
    const trimmedKin = nextOfKinPhone.trim();
    const formattedKin = trimmedKin !== "" ? toInternationalPhone(trimmedKin) : "";

    updateProfile({
      name: trimmedName,
      nextOfKinPhone: formattedKin,
      bio: bio.trim(),
    });

    const patch: { display_name?: string; next_of_kin_phone?: string } = {};
    if (trimmedName !== "") {
      patch.display_name = trimmedName;
    }
    patch.next_of_kin_phone = formattedKin;
    updateServerProfile.mutate(patch);
    setProfileFeedback("Saved to your account and this phone.");
  }

  /** Canonical server suburb, or null for a write-in the backend doesn't know (it would 422). */
  function knownSuburb(value: string): string | null {
    const clean = value.trim().toLowerCase();
    return availableSuburbs.find((item) => item.toLowerCase() === clean) ?? null;
  }

  function handleSaveWorkerReach(): void {
    const cleanSuburb = knownSuburb(suburbDraft);
    updateProfile({
      travelKm,
      homeSuburb: cleanSuburb ?? suburbDraft.trim(),
      travelMeans,
    });
    updateServerProfile.mutate({
      travel_km: travelKm,
      ...(cleanSuburb !== null ? { home_suburb: cleanSuburb } : {}),
    });
    if (cleanSuburb !== null) {
      const alreadyRegistered = (serviceAreas.data ?? []).some(
        (area) =>
          area.suburb.toLowerCase() === cleanSuburb.toLowerCase() &&
          (area.travel_means ?? "") === travelMeans,
      );
      if (!alreadyRegistered) {
        registerServiceArea.mutate({ suburb: cleanSuburb, travel_means: travelMeans });
      }
    }
    setLocationFeedback(
      cleanSuburb !== null || suburbDraft.trim() === ""
        ? "Work reach and suburb saved."
        : "Work reach saved. Pick a suburb from the list so clients nearby can find you.",
    );
  }

  function handleSaveEmployerDefaults(): void {
    const typedSuburb = suburbDraft.trim();
    const cleanSuburb = knownSuburb(typedSuburb);
    updateProfile({
      homeSuburb: cleanSuburb ?? typedSuburb,
      lastSuburb: cleanSuburb ?? typedSuburb,
      lastAddress: defaultAddress.trim(),
      defaultLandmark: defaultLandmark.trim(),
      preferredCurrency,
    });
    if (cleanSuburb !== null) {
      updateServerProfile.mutate({ home_suburb: cleanSuburb });
    }
    setLocationFeedback("Default job location and payment preferences saved.");
  }

  async function handleIdPhotoFiles(files: File[]): Promise<void> {
    const file = files[0];
    if (!file) return;
    setVettingError(null);
    setVettingFeedback(null);
    // ADR-005: the ID tier is earned by a real photo. Never submit a made-up URL.
    if (!canUpload) {
      setVettingError("Photo uploads are not available right now. Try again when you have signal.");
      return;
    }
    let url: string;
    try {
      url = await upload(file, "photo");
    } catch (failure: unknown) {
      setVettingError(
        isUploadUnavailable(failure)
          ? "Photo uploads are not available right now. Try again when you have signal."
          : failure instanceof Error
            ? failure.message
            : "Could not upload ID photo.",
      );
      return;
    }
    try {
      await submitIdPhoto.mutateAsync({ id_photo_url: url });
      setVettingFeedback("National ID photo submitted. Your standing is now ID checked.");
    } catch (failure: unknown) {
      setVettingError(
        failure instanceof Error ? failure.message : "Could not submit ID verification.",
      );
    }
  }

  async function handleAddReference(event: React.FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const cleanName = refName.trim();
    const cleanPhone = refPhone.trim();
    if (cleanName.length < 2 || cleanPhone.replace(/\D/g, "").length < 7) {
      setVettingError("Enter the reference's name and a valid phone number.");
      return;
    }
    setVettingError(null);
    setVettingFeedback(null);
    try {
      await addReference.mutateAsync({
        name: cleanName,
        phone: toInternationalPhone(cleanPhone),
      });
      setRefName("");
      setRefPhone("");
      setVettingFeedback(
        "Reference added. This counts toward your Apprentice & Journeyman vetting.",
      );
    } catch (failure: unknown) {
      setVettingError(failure instanceof Error ? failure.message : "Could not add reference.");
    }
  }

  async function handleVouchSubmit(event: React.FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const cleanId = vouchWorkerId.trim();
    if (cleanId === "") return;
    setVettingError(null);
    setVettingFeedback(null);
    try {
      await vouchForWorker.mutateAsync({ worker_id: cleanId });
      setVouchWorkerId("");
      setVettingFeedback("Your peer vouch has been recorded.");
    } catch (failure: unknown) {
      setVettingError(failure instanceof Error ? failure.message : "Could not record peer vouch.");
    }
  }

  function handleCopyWorkerId(): void {
    if (!user?.id) return;
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      void navigator.clipboard.writeText(user.id);
    }
    setCopiedWorkerId(true);
    setTimeout(() => setCopiedWorkerId(false), 2500);
  }

  const normalisedDraft = suburbDraft.trim().toLowerCase();
  const suburbMenu: ReactNode =
    predictedSuburbs.length > 0 ? (
      <ul
        id={suburbListboxId}
        role="listbox"
        aria-label="Matching suburbs"
        className="combobox__menu"
      >
        {predictedSuburbs.map((option) => {
          const isSelected = option.toLowerCase() === normalisedDraft;
          return (
            <li key={option} role="option" aria-selected={isSelected}>
              <button
                type="button"
                className={
                  isSelected ? "combobox__option combobox__option--active" : "combobox__option"
                }
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => {
                  setSuburbOverride(option);
                  setIsSuburbOpen(false);
                  setLocationFeedback(null);
                }}
              >
                <span>{option}</span>
                {isSelected && <span className="combobox__badge">Selected</span>}
              </button>
            </li>
          );
        })}
      </ul>
    ) : null;

  const isPersonalUnchanged =
    name.trim() === (profile.name || user?.display_name || "") &&
    nextOfKinPhone.trim() === formatLocalPhone(user?.next_of_kin_phone ?? profile.nextOfKinPhone) &&
    bio.trim() === profile.bio;

  return (
    <Screen glow={isWorker ? "worker" : "employer"} hasTabBar>
      <header className="topbar topbar--split">
        <div>
          <div className="meta" style={{ fontSize: 13 }}>
            Maritcho account
          </div>
          <h1 className="title title--page">{isWorker ? "My profile" : "Account"}</h1>
        </div>
        {isWorker && user?.id && (
          <Link href={`/employer/workers/${user.id}`} className="btn btn--sm btn--soft">
            <Icon name="user" size={15} />
            Public view
          </Link>
        )}
      </header>

      {/* Hero Identity Card */}
      <section className="card stack" style={{ gap: 14 }}>
        <div className="row" style={{ gap: 14, alignItems: "center" }}>
          <Avatar
            name={displayName}
            seed={user?.id ?? displayName}
            size="lg"
            isOnline={isWorker ? profile.isAvailable : true}
          />
          <div className="grow">
            <div className="row row--tight">
              <div style={{ fontSize: 18, fontWeight: 700 }}>{displayName}</div>
              {isWorker && isVerifiedGrade(currentGrade) && (
                <span className="text-emerald" style={{ display: "inline-flex" }}>
                  <Icon name="shieldCheck" size={18} label="Checked by Maritcho" />
                </span>
              )}
            </div>
            <div className="meta meta--secondary" style={{ marginTop: 2 }}>
              +263 {displayPhone} · {isWorker ? "Finds work" : "Hires help"}
              {user?.created_at ? ` · Joined ${formatShortDate(user.created_at)}` : ""}
            </div>
            <div className="chip-list" style={{ marginTop: 8, gap: 6 }}>
              <span
                className={isWorker && isVerifiedGrade(currentGrade) ? "tag tag--verified" : "tag"}
              >
                {isWorker ? gradeLabel(currentGrade) : "Verified Employer"}
              </span>
              {suburbDraft.trim() !== "" && (
                <span className="tag">
                  <Icon name="pin" size={12} />
                  {suburbDraft.trim()}
                </span>
              )}
              {!isWorker && <span className="tag">Pays in {preferredCurrency}</span>}
            </div>
          </div>
        </div>

        {/* Role / Mode Switcher (WEB-011: One account hires and finds work) */}
        <div
          className="stack"
          style={{
            gap: 6,
            paddingTop: 10,
            borderTop: "1px solid var(--line)",
          }}
        >
          <div className="row row--between">
            <span className="meta meta--secondary" style={{ fontSize: 12, fontWeight: 600 }}>
              Use Maritcho right now to
            </span>
            {isSwitchingRole && <span className="meta">Switching…</span>}
          </div>
          <div className="segmented segmented--choice" role="group" aria-label="Account mode">
            <button
              type="button"
              className="segmented__tab"
              aria-pressed={!isWorker}
              disabled={isSwitchingRole}
              onClick={() => void handleRoleSwitch("BUYER")}
            >
              Hire help (Employer)
            </button>
            <button
              type="button"
              className="segmented__tab"
              aria-pressed={isWorker}
              disabled={isSwitchingRole}
              onClick={() => void handleRoleSwitch("WORKER")}
            >
              Find work (Worker)
            </button>
          </div>
        </div>
      </section>

      {/* ==================== WORKER ACCOUNT SECTIONS ==================== */}
      {isWorker && (
        <>
          {/* 1. Standing, Earnings & Performance Dashboard */}
          <section className="card stack" style={{ gap: 12 }} aria-labelledby="acc-standing-title">
            <div className="row row--between">
              <div>
                <h2 id="acc-standing-title" style={{ fontSize: 15, fontWeight: 700 }}>
                  Standing &amp; earnings
                </h2>
                <div className="meta meta--secondary" style={{ marginTop: 2 }}>
                  {monthLabel()} · Total earned {formatMoney(workerTotalEarned)}
                </div>
              </div>
              <Link href="/worker/work" className="text-link">
                My work
              </Link>
            </div>

            <div className="stat-grid">
              <div className="stat-tile">
                <div className="stat__value text-amber">
                  {formatMoney(workerMonthSummary.earned)}
                </div>
                <div className="stat__label">This month ({workerMonthSummary.jobsDone})</div>
              </div>
              <div className="stat-tile">
                <div className="stat__value">
                  {hasWorkerHistory ? formatPercent(standing.data?.on_time_rate ?? 100) : "100%"}
                </div>
                <div className="stat__label">On time</div>
              </div>
              <div className="stat-tile">
                <div className="stat__value">{standing.data?.jobs_completed ?? 0}</div>
                <div className="stat__label">Jobs done ({workerActiveAssignedCount} active)</div>
              </div>
              <div className="stat-tile">
                <div className="stat__value">
                  {standing.data?.rating_average !== null &&
                  standing.data?.rating_average !== undefined
                    ? `★ ${standing.data.rating_average.toFixed(1)}`
                    : hasWorkerHistory
                      ? formatPercent(standing.data?.fill_rate ?? 100)
                      : "New"}
                </div>
                <div className="stat__label">
                  {standing.data?.rating_average !== null &&
                  standing.data?.rating_average !== undefined
                    ? `Rating (${standing.data.rating_count ?? 0})`
                    : `${(myOffers.data ?? []).length} open offers`}
                </div>
              </div>
            </div>

            {standing.data?.is_frozen ? (
              <div className="banner banner--quiet" role="alert" style={{ borderRadius: 12 }}>
                <Icon name="shield" size={18} />
                <div className="grow">
                  <div style={{ fontWeight: 700, fontSize: 13 }}>
                    New matches paused while a job dispute is open
                  </div>
                  <div className="meta">
                    Respond on the disputed job in My Work to unfreeze your standing.
                  </div>
                </div>
                <Link href="/worker/work" className="btn btn--sm">
                  Resolve
                </Link>
              </div>
            ) : (
              <div className="row row--between meta meta--secondary" style={{ fontSize: 12 }}>
                <span>
                  Standing health:{" "}
                  <strong style={{ color: "var(--text)" }}>
                    {formatPercent(standing.data?.dispute_rate ?? 0)} disputed
                  </strong>
                </span>
                <span>
                  Fill rate:{" "}
                  <strong style={{ color: "var(--text)" }}>
                    {hasWorkerHistory ? formatPercent(standing.data?.fill_rate ?? 100) : "Ready"}
                  </strong>
                </span>
              </div>
            )}
          </section>

          {/* 2. Availability, Suburb & Work Reach */}
          <section className="card stack" style={{ gap: 14 }} aria-labelledby="acc-reach-title">
            <div className="row row--between">
              <div>
                <h2 id="acc-reach-title" style={{ fontSize: 15, fontWeight: 700 }}>
                  Availability &amp; travel reach
                </h2>
                <div className="meta meta--secondary" style={{ marginTop: 2 }}>
                  Control when clients can book you and how far you travel
                </div>
              </div>
              <Switch
                isOn={profile.isAvailable}
                label="Available for work"
                onToggle={(next) => {
                  updateProfile({ isAvailable: next });
                  updateServerProfile.mutate({ is_available: next });
                }}
              />
            </div>

            <div className="field">
              <div className="row row--between">
                <label htmlFor="acc-travel-km" className="field__label">
                  Maximum travel distance
                </label>
                <span className="text-amber" style={{ fontSize: 14, fontWeight: 700 }}>
                  {travelKm} km
                </span>
              </div>
              <input
                id="acc-travel-km"
                className="range"
                type="range"
                min={MIN_TRAVEL_KM}
                max={MAX_TRAVEL_KM}
                value={travelKm}
                aria-valuetext={`${travelKm} kilometres`}
                onChange={(event) => {
                  setTravelDraft(clampTravelKm(Number(event.target.value)));
                  setLocationFeedback(null);
                }}
              />
            </div>

            <div className="field">
              <label htmlFor="acc-suburb-input" className="field__label">
                Home suburb (type or pick)
              </label>
              <div className="combobox">
                <input
                  id="acc-suburb-input"
                  className="input"
                  role="combobox"
                  aria-expanded={isSuburbOpen}
                  aria-controls={suburbListboxId}
                  aria-autocomplete="list"
                  placeholder="Type or choose your suburb…"
                  value={suburbDraft}
                  onFocus={() => setIsSuburbOpen(true)}
                  onBlur={() => setTimeout(() => setIsSuburbOpen(false), 150)}
                  onChange={(event) => {
                    setSuburbOverride(event.target.value);
                    setIsSuburbOpen(true);
                    setLocationFeedback(null);
                  }}
                />
                {isSuburbOpen && suburbMenu}
              </div>
            </div>

            <div className="field">
              <span className="field__label">How you travel to jobs</span>
              <div className="chip-list" style={{ marginTop: 6, gap: 6 }}>
                {TRAVEL_MEANS_OPTIONS.map((mode) => (
                  <button
                    key={mode}
                    type="button"
                    className={travelMeans === mode ? "tag tag--verified" : "tag"}
                    onClick={() => {
                      setTravelMeans(mode);
                      setLocationFeedback(null);
                    }}
                  >
                    {mode}
                  </button>
                ))}
              </div>
            </div>

            <button type="button" className="btn btn--soft" onClick={handleSaveWorkerReach}>
              Save work reach
            </button>
            {locationFeedback && (
              <p className="meta text-emerald" role="status">
                {locationFeedback}
              </p>
            )}
          </section>

          {/* 3. Progressive Vetting & Trust Tiers (ADR-005) */}
          <section className="card stack" style={{ gap: 14 }} aria-labelledby="acc-vetting-title">
            <div className="row row--between">
              <div>
                <h2 id="acc-vetting-title" style={{ fontSize: 15, fontWeight: 700 }}>
                  Vetting &amp; trust tier
                </h2>
                <div className="meta meta--secondary" style={{ marginTop: 2 }}>
                  Current tier: <strong>{gradeLabel(currentGrade)}</strong> — higher tiers rank
                  first for jobs
                </div>
              </div>
              <span className={isVerifiedGrade(currentGrade) ? "badge badge--emerald" : "badge"}>
                {gradeLabel(currentGrade)}
              </span>
            </div>

            {/* 5-Stage Tier Progression */}
            <div className="chip-list" style={{ gap: 6 }}>
              {GRADE_TIERS.map((tier, index) => {
                const unlocked = index <= currentGradeRank;
                return (
                  <span
                    key={tier.grade}
                    className={unlocked ? "tag tag--verified" : "tag"}
                    title={tier.requirement}
                  >
                    {unlocked && <Icon name="check" size={12} strokeWidth={2.4} />}
                    {tier.shortLabel}
                  </span>
                );
              })}
            </div>

            {/* Step 1: National ID photo */}
            <div
              className="card card--compact stack"
              style={{ gap: 8, background: "var(--bg-subtle)" }}
            >
              <div className="row row--between">
                <div className="row row--tight">
                  <Icon
                    name={hasIdVerified ? "shieldCheck" : "shield"}
                    size={16}
                    className={hasIdVerified ? "text-emerald" : "text-muted"}
                  />
                  <span style={{ fontSize: 14, fontWeight: 700 }}>
                    1. National ID check (ID checked tier)
                  </span>
                </div>
                <span className="meta">{hasIdVerified ? "Submitted" : "Required"}</span>
              </div>
              <p className="meta meta--secondary" style={{ lineHeight: 1.45 }}>
                {hasIdVerified
                  ? "Your National ID evidence is on file. Clients see the Checked by Maritcho badge."
                  : "Take a clear photo of your National ID to unlock the ID checked badge."}
              </p>
              <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
                <button
                  type="button"
                  className="btn btn--sm btn--soft"
                  disabled={isUploadingMedia || submitIdPhoto.isPending}
                  onClick={() => setIsIdPickerOpen(true)}
                >
                  <Icon name="camera" size={15} />
                  {hasIdVerified ? "Replace ID photo" : "Upload ID photo"}
                </button>
              </div>
            </div>

            {/* Step 2: Contactable References */}
            <div
              className="card card--compact stack"
              style={{ gap: 8, background: "var(--bg-subtle)" }}
            >
              <div className="row row--between">
                <div className="row row--tight">
                  <Icon
                    name={referenceCount > 0 ? "check" : "users"}
                    size={16}
                    className={referenceCount > 0 ? "text-emerald" : "text-muted"}
                  />
                  <span style={{ fontSize: 14, fontWeight: 700 }}>
                    2. Client references (Apprentice tier)
                  </span>
                </div>
                <span className="meta">{referenceCount} on file</span>
              </div>
              <p className="meta meta--secondary" style={{ lineHeight: 1.45 }}>
                Add someone you&apos;ve worked for who can confirm your work. With your ID checked,
                1 reference promotes you to Apprentice.
              </p>
              {referenceList.length > 0 && (
                <div className="stack" style={{ gap: 4 }}>
                  {referenceList.map((ref) => (
                    <div key={ref.id} className="row row--between meta" style={{ fontSize: 12 }}>
                      <strong style={{ color: "var(--text)" }}>{ref.name}</strong>
                      <span>+263 {formatLocalPhone(ref.phone)}</span>
                    </div>
                  ))}
                </div>
              )}
              <form
                className="stack"
                style={{ gap: 8 }}
                onSubmit={(e) => void handleAddReference(e)}
              >
                <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
                  <input
                    className="input grow"
                    placeholder="Reference name (e.g. Mai Ncube)"
                    aria-label="Reference name"
                    value={refName}
                    maxLength={100}
                    onChange={(event) => setRefName(event.target.value)}
                  />
                  <input
                    className="input grow"
                    placeholder="Phone (e.g. 077 123 4567)"
                    aria-label="Reference phone"
                    value={refPhone}
                    maxLength={20}
                    onChange={(event) => setRefPhone(event.target.value)}
                  />
                </div>
                <button
                  type="submit"
                  className="btn btn--sm btn--soft"
                  disabled={addReference.isPending}
                >
                  {addReference.isPending ? "Adding…" : "Add reference"}
                </button>
              </form>
            </div>

            {/* Step 3: Peer Vouches */}
            <div
              className="card card--compact stack"
              style={{ gap: 8, background: "var(--bg-subtle)" }}
            >
              <div className="row row--between">
                <div className="row row--tight">
                  <Icon
                    name={vouchCount > 0 ? "shieldCheck" : "star"}
                    size={16}
                    className={vouchCount > 0 ? "text-emerald" : "text-muted"}
                  />
                  <span style={{ fontSize: 14, fontWeight: 700 }}>
                    3. Peer vouches (Journeyman &amp; Expert)
                  </span>
                </div>
                <span className="meta">{vouchCount} / 3 vouches</span>
              </div>
              <p className="meta meta--secondary" style={{ lineHeight: 1.45 }}>
                1 vouch from a Journeyman or Expert promotes you to Journeyman; 3 vouches promote
                you to Expert. Share your Worker ID with a senior tradesperson to get vouched.
              </p>
              {user?.id && (
                <div className="row row--between" style={{ gap: 8 }}>
                  <code
                    className="meta"
                    style={{
                      padding: "6px 10px",
                      borderRadius: 8,
                      background: "var(--bg-elevated)",
                      fontSize: 12,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}
                  >
                    {user.id}
                  </code>
                  <button type="button" className="btn btn--sm" onClick={handleCopyWorkerId}>
                    {copiedWorkerId ? "Copied" : "Copy ID"}
                  </button>
                </div>
              )}

              {canVouchForPeers && (
                <form
                  className="row"
                  style={{ gap: 8, marginTop: 4 }}
                  onSubmit={(e) => void handleVouchSubmit(e)}
                >
                  <input
                    className="input grow"
                    placeholder="Enter fellow worker's ID to vouch for them"
                    aria-label="Fellow worker ID"
                    value={vouchWorkerId}
                    onChange={(event) => setVouchWorkerId(event.target.value)}
                  />
                  <button
                    type="submit"
                    className="btn btn--sm btn--soft"
                    disabled={vouchWorkerId.trim() === "" || vouchForWorker.isPending}
                  >
                    Vouch
                  </button>
                </form>
              )}
            </div>

            {vettingFeedback && (
              <p className="meta text-emerald" role="status">
                {vettingFeedback}
              </p>
            )}
            {vettingError && (
              <p className="field-error" role="alert">
                {vettingError}
              </p>
            )}
          </section>

          {/* 4. Registered Skills & Service Areas Summary */}
          <section className="card stack" style={{ gap: 10 }}>
            <div className="row row--between">
              <div style={{ fontSize: 15, fontWeight: 700 }}>Registered skills &amp; areas</div>
              <span className="meta">{(skills.data ?? []).length} trades</span>
            </div>
            {(skills.data ?? []).length > 0 ? (
              <div className="chip-list" style={{ gap: 6 }}>
                {(skills.data ?? []).map((skill) => (
                  <span key={skill.id} className="tag">
                    <Icon name={tradeIcon(skill.trade)} size={13} />
                    {tradeLabel(skill.trade)}
                  </span>
                ))}
              </div>
            ) : (
              <p className="meta meta--secondary">
                No trades added yet. Add your skills so clients nearby can hire you.
              </p>
            )}

            <Link href="/worker/skills" className="list-row" style={{ marginTop: 4 }}>
              <div className="icon-tile icon-tile--emerald">
                <Icon name="briefcase" />
              </div>
              <div className="grow">
                <div style={{ fontWeight: 700 }}>Skills &amp; travel distance</div>
                <div className="meta">Change what work you’re shown</div>
              </div>
              <Icon name="chevronRight" strokeWidth={2} />
            </Link>
          </section>

          <PhotoPicker
            isOpen={isIdPickerOpen}
            onClose={() => setIsIdPickerOpen(false)}
            onPick={(files) => void handleIdPhotoFiles(files)}
          />
        </>
      )}

      {/* ==================== EMPLOYER ACCOUNT SECTIONS ==================== */}
      {!isWorker && (
        <>
          {/* 1. Employer Hiring Overview & Activity Dashboard */}
          <section className="card stack" style={{ gap: 12 }} aria-labelledby="acc-employer-stats">
            <div className="row row--between">
              <div>
                <h2 id="acc-employer-stats" style={{ fontSize: 15, fontWeight: 700 }}>
                  Hiring overview
                </h2>
                <div className="meta meta--secondary" style={{ marginTop: 2 }}>
                  Summary of your jobs, incoming quotes, and completed work
                </div>
              </div>
              <Link href="/employer/jobs" className="text-link">
                All jobs
              </Link>
            </div>

            <div className="stat-grid">
              <div className="stat-tile">
                <div className="stat__value text-amber">{employerActiveList.length}</div>
                <div className="stat__label">Active jobs</div>
              </div>
              <div className="stat-tile">
                <div className="stat__value">{employerWaitingOffers}</div>
                <div className="stat__label">Offers waiting</div>
              </div>
              <div className="stat-tile">
                <div className="stat__value">{employerDoneList.length}</div>
                <div className="stat__label">Completed</div>
              </div>
              <div className="stat-tile">
                <div className="stat__value">
                  {formatMoney(employerTotalSpent, preferredCurrency)}
                </div>
                <div className="stat__label">Signed-off total</div>
              </div>
            </div>

            <div className="btn-grid">
              <Link href="/employer/post" className="btn btn--primary">
                <Icon name="plus" size={16} />
                Post a job
              </Link>
              <Link href="/employer/workers" className="btn btn--soft">
                <Icon name="users" size={16} />
                Find workers
              </Link>
            </div>
          </section>

          {/* 2. Saved Job Location & Payment Defaults (ADR-002 & ADR-004) */}
          <section
            className="card stack"
            style={{ gap: 14 }}
            aria-labelledby="acc-employer-defaults"
          >
            <div>
              <h2 id="acc-employer-defaults" style={{ fontSize: 15, fontWeight: 700 }}>
                Saved job location &amp; payment defaults
              </h2>
              <div className="meta meta--secondary" style={{ marginTop: 2 }}>
                Prefills where your jobs are located and ranks nearby workers around your suburb
              </div>
            </div>

            <div className="field">
              <label htmlFor="acc-employer-suburb" className="field__label">
                Default suburb (type or pick)
              </label>
              <div className="combobox">
                <input
                  id="acc-employer-suburb"
                  className="input"
                  role="combobox"
                  aria-expanded={isSuburbOpen}
                  aria-controls={suburbListboxId}
                  aria-autocomplete="list"
                  placeholder="Type or choose your suburb…"
                  value={suburbDraft}
                  onFocus={() => setIsSuburbOpen(true)}
                  onBlur={() => setTimeout(() => setIsSuburbOpen(false), 150)}
                  onChange={(event) => {
                    setSuburbOverride(event.target.value);
                    setIsSuburbOpen(true);
                    setLocationFeedback(null);
                  }}
                />
                {isSuburbOpen && suburbMenu}
              </div>
            </div>

            <div className="field">
              <label htmlFor="acc-default-address" className="field__label">
                Default house number or street
              </label>
              <input
                id="acc-default-address"
                className="input"
                placeholder="e.g. 1428 Nkulumane 12"
                value={defaultAddress}
                maxLength={500}
                onChange={(event) => {
                  setDefaultAddress(event.target.value);
                  setLocationFeedback(null);
                }}
              />
            </div>

            <div className="field">
              <label htmlFor="acc-default-landmark" className="field__label">
                Default landmark directions (shared only with hired worker)
              </label>
              <input
                id="acc-default-landmark"
                className="input"
                placeholder="e.g. Green gate opposite the clinic"
                value={defaultLandmark}
                maxLength={300}
                onChange={(event) => {
                  setDefaultLandmark(event.target.value);
                  setLocationFeedback(null);
                }}
              />
            </div>

            <div className="field">
              <span className="field__label">Preferred payment currency</span>
              <div
                className="segmented segmented--choice"
                role="group"
                aria-label="Preferred payment currency"
                style={{ marginTop: 6 }}
              >
                {(["USD", "ECOCASH", "ZWG"] as const).map((curr) => (
                  <button
                    key={curr}
                    type="button"
                    className="segmented__tab"
                    aria-pressed={preferredCurrency === curr}
                    onClick={() => {
                      setPreferredCurrency(curr);
                      setLocationFeedback(null);
                    }}
                  >
                    {curr === "USD" ? "Cash (USD)" : curr === "ECOCASH" ? "EcoCash" : "ZWG"}
                  </button>
                ))}
              </div>
            </div>

            <button type="button" className="btn btn--soft" onClick={handleSaveEmployerDefaults}>
              Save hiring defaults
            </button>
            {locationFeedback && (
              <p className="meta text-emerald" role="status">
                {locationFeedback}
              </p>
            )}
          </section>
        </>
      )}

      {/* ==================== PERSONAL & SAFETY DETAILS (BOTH ROLES) ==================== */}
      <form className="card stack" style={{ gap: 12 }} onSubmit={handleSavePersonalDetails}>
        <div>
          <h2 style={{ fontSize: 15, fontWeight: 700 }}>Personal &amp; safety details</h2>
          <div className="meta meta--secondary" style={{ marginTop: 2 }}>
            Your display name and emergency contact on Maritcho
          </div>
        </div>

        <div className="field">
          <label htmlFor="acc-name" className="field__label">
            Name shown in the app
          </label>
          <input
            id="acc-name"
            className="input"
            value={name}
            maxLength={80}
            onChange={(event) => {
              setNameDraft(event.target.value);
              setProfileFeedback(null);
            }}
          />
        </div>

        <div className="field">
          <label htmlFor="acc-kin-phone" className="field__label">
            Next of kin / emergency phone (+263)
          </label>
          <input
            id="acc-kin-phone"
            className="input"
            placeholder="e.g. 077 200 0111"
            value={nextOfKinPhone}
            maxLength={20}
            onChange={(event) => {
              setNextOfKinPhoneDraft(event.target.value);
              setProfileFeedback(null);
            }}
          />
        </div>

        {isWorker && (
          <div className="field">
            <label htmlFor="acc-bio" className="field__label">
              Short trade summary (specialty &amp; tools)
            </label>
            <input
              id="acc-bio"
              className="input"
              placeholder="e.g. Geysers, solar inverters, borehole pumps"
              value={bio}
              maxLength={240}
              onChange={(event) => {
                setBio(event.target.value);
                setProfileFeedback(null);
              }}
            />
          </div>
        )}

        <button type="submit" className="btn btn--soft" disabled={isPersonalUnchanged}>
          Save details
        </button>
        {profileFeedback ? (
          <p className="meta text-emerald" role="status">
            {profileFeedback}
          </p>
        ) : (
          <p className="meta">Saved on this phone and synced to your Maritcho account.</p>
        )}
      </form>

      {/* Legal & Sign Out */}
      <section className="card stack" style={{ gap: 8 }}>
        <div className="row row--between meta">
          <Link href="/terms" className="text-link">
            Terms of Service
          </Link>
          <Link href="/privacy" className="text-link">
            Privacy Policy
          </Link>
        </div>
        <button type="button" className="btn btn--block" onClick={() => void signOut()}>
          <Icon name="logout" size={18} />
          Sign out
        </button>
      </section>

      {gradeToCelebrate !== null && (
        <Celebration
          title={`You're now ${gradeLabel(gradeToCelebrate)}`}
          detail="Clients nearby see your new badge, and higher tiers are shown first."
          onDone={() => updateProfile({ celebratedGrade: gradeToCelebrate })}
        />
      )}

      {tabBar}
    </Screen>
  );
}
