"use client";

import { useState, type FormEvent } from "react";
import { onlineManager } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { BackButton } from "@/components/ui/BackButton";
import { Icon } from "@/components/ui/Icon";
import { PhotoStrip } from "@/components/ui/PhotoStrip";
import { Screen } from "@/components/ui/Screen";
import type { Trade } from "@/core/api/schemas";
import {
  ALL_SKILLS,
  describeWithSkill,
  findSkill,
  tradeIcon,
  tradeLabel,
  type SkillOption,
} from "@/core/format/trades";
import { isUploadUnavailable } from "@/core/media/upload";
import { useDictation } from "@/core/media/use-dictation";
import { useMediaUploads } from "@/core/media/use-media-uploads";
import { useUpload } from "@/core/media/use-upload";
import { updateProfile, useLocalProfile } from "@/core/session/profile-store";
import { useCreateJob } from "@/features/jobs/hooks";
import { withTiming } from "@/features/jobs/job-helpers";
import { LocationSheet, type JobLocation } from "@/features/jobs/LocationSheet";
import { TradePickerSheet } from "@/features/jobs/TradePickerSheet";

const DESCRIPTION_LIMIT = 300;

type Timing = "Today" | "This week" | "date";

type Props = {
  initialTrade: Trade | null;
  initialSkillId: string | null;
  shouldOpenPicker: boolean;
};

function initialSkill(trade: Trade | null, skillId: string | null): SkillOption | null {
  const bySkill = findSkill(skillId);
  if (bySkill?.trade) return bySkill;
  if (trade === null) return null;
  return (
    ALL_SKILLS.find((skill) => skill.trade === trade && skill.label === tradeLabel(trade)) ??
    ALL_SKILLS.find((skill) => skill.trade === trade) ??
    null
  );
}

export function validatePostJob(
  skill: SkillOption | null,
  description: string,
  location: JobLocation,
): string | null {
  if (skill === null || skill.trade === null) return "Pick who you need first.";
  if (description.trim().length < 5)
    return "Say a few words about the job — or tap the mic and say it.";
  if (location.suburb === "" || location.address.trim() === "") return "Tell us where the job is.";
  return null;
}

/** Design E2 · Post a job. */
export function PostJobScreen({ initialTrade, initialSkillId, shouldOpenPicker }: Props) {
  const router = useRouter();
  const profile = useLocalProfile();
  const createJob = useCreateJob();
  const canUpload = useMediaUploads();
  const { upload, isUploading } = useUpload();

  const [skill, setSkill] = useState<SkillOption | null>(() =>
    initialSkill(initialTrade, initialSkillId),
  );
  const [isPickerOpen, setIsPickerOpen] = useState(shouldOpenPicker || skill === null);
  const [isLocationOpen, setIsLocationOpen] = useState(false);
  const [description, setDescription] = useState("");
  const [location, setLocation] = useState<JobLocation>({
    suburb: profile.lastSuburb,
    address: profile.lastAddress,
    landmark: "",
  });
  const [timing, setTiming] = useState<Timing>("Today");
  const [date, setDate] = useState("");
  const [budget, setBudget] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [photos, setPhotos] = useState<File[]>([]);
  const [hasPhotoFailed, setHasPhotoFailed] = useState(false);

  const dictation = useDictation((text) =>
    setDescription((current) =>
      `${current}${current.trim() === "" ? "" : " "}${text}`.slice(0, DESCRIPTION_LIMIT),
    ),
  );

  function timingLabel(): string {
    if (timing !== "date") return timing;
    return date === ""
      ? "Flexible"
      : new Date(date).toLocaleDateString("en-GB", {
          weekday: "short",
          day: "numeric",
          month: "short",
        });
  }

  /** Upload the photo if it can go now; `undefined` means post without one. */
  async function photoUrlFor(photo: File | undefined): Promise<string | undefined | "failed"> {
    if (photo === undefined || !canUpload || !onlineManager.isOnline()) return undefined;
    try {
      return await upload(photo, "photo");
    } catch (failure: unknown) {
      if (isUploadUnavailable(failure)) return undefined;
      setFormError(
        `The photo didn't send${failure instanceof Error ? ` (${failure.message})` : ""}. Try again, or post without it.`,
      );
      setHasPhotoFailed(true);
      return "failed";
    }
  }

  async function submit(isWithoutPhoto: boolean): Promise<void> {
    const problem = validatePostJob(skill, description, location);
    setFormError(problem);
    if (problem !== null || skill === null || skill.trade === null) return;

    const photoUrl = isWithoutPhoto ? undefined : await photoUrlFor(photos[0]);
    if (photoUrl === "failed") return;
    setHasPhotoFailed(false);

    const budgetAmount = Number(budget);
    updateProfile({ lastSuburb: location.suburb, lastAddress: location.address });
    const input = {
      trade: skill.trade,
      suburb: location.suburb,
      address: location.address,
      ...(location.landmark === "" ? {} : { landmark_narrative: location.landmark }),
      problem_description: withTiming(describeWithSkill(skill, description), timingLabel()),
      ...(budget !== "" && budgetAmount > 0 ? { budget_amount: budgetAmount } : {}),
      ...(photoUrl === undefined ? {} : { problem_photo_url: photoUrl }),
    };

    if (!onlineManager.isOnline()) {
      // Queued and persisted; it posts itself when the connection returns.
      createJob.mutate(input);
      router.push("/employer?queued=1");
      return;
    }
    createJob.mutate(input, { onSuccess: (job) => router.replace(`/employer/jobs/${job.id}`) });
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    void submit(false);
  }

  const locationText =
    location.address === ""
      ? "Add the address"
      : `${location.address}${location.suburb ? `, ${location.suburb}` : ""}`;

  return (
    <Screen bodyClassName="">
      <form onSubmit={handleSubmit} className="stack" style={{ flex: 1, gap: 12 }} noValidate>
        <div className="topbar">
          <BackButton fallbackHref="/employer" />
          <h1 className="title">Post a job</h1>
        </div>

        <button
          type="button"
          className="card card--compact row"
          style={{ gap: 14, textAlign: "left" }}
          onClick={() => setIsPickerOpen(true)}
        >
          <div
            className="icon-tile icon-tile--amber icon-tile--edged"
            style={{ width: 42, height: 42 }}
          >
            <Icon name={skill?.trade ? tradeIcon(skill.trade) : "search"} />
          </div>
          <div className="grow">
            <div className="label">What needs doing?</div>
            <div style={{ marginTop: 2, fontSize: 16, fontWeight: 700 }}>
              {skill?.label ?? "Pick a skill"}
            </div>
          </div>
          <span className="text-link">{skill ? "Change" : "Choose"}</span>
        </button>

        <div className="card card--compact" style={{ padding: "14px 16px" }}>
          <div className="row row--between row--baseline">
            <label htmlFor="pj-desc" style={{ fontSize: 14, fontWeight: 700 }}>
              Describe the job
            </label>
            <span className="meta">
              {description.length} / {DESCRIPTION_LIMIT}
            </span>
          </div>
          <textarea
            id="pj-desc"
            rows={4}
            className="textarea textarea--lined"
            style={{ marginTop: 10 }}
            placeholder="e.g. Pipe under the kitchen sink is leaking. Water is off for now."
            maxLength={DESCRIPTION_LIMIT}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
          <div className="row" style={{ marginTop: 10, gap: 8 }}>
            <PhotoStrip max={1} onChange={setPhotos} />
            {dictation.isSupported && (
              <button
                type="button"
                className={dictation.isListening ? "icon-btn round-btn--recording" : "icon-btn"}
                style={{ width: 52, height: 52 }}
                aria-label={dictation.isListening ? "Stop listening" : "Say it instead of typing"}
                aria-pressed={dictation.isListening}
                onClick={dictation.isListening ? dictation.stop : dictation.start}
              >
                <Icon name={dictation.isListening ? "stop" : "mic"} />
              </button>
            )}
          </div>
          {photos.length > 0 && !canUpload && (
            <p className="meta" style={{ marginTop: 8 }}>
              The photo stays on your phone for now. Say what&apos;s wrong in words too.
            </p>
          )}
        </div>

        <button
          type="button"
          className="card card--compact row"
          style={{ gap: 14, textAlign: "left" }}
          onClick={() => setIsLocationOpen(true)}
        >
          <div className="icon-tile icon-tile--emerald" style={{ width: 42, height: 42 }}>
            <Icon name="pin" />
          </div>
          <div className="grow">
            <div className="label">Where is the job?</div>
            <div style={{ marginTop: 2, fontSize: 15, fontWeight: 700 }} className="truncate">
              {locationText}
            </div>
          </div>
          <Icon name="chevronRight" strokeWidth={2} />
        </button>

        <fieldset className="card card--compact" style={{ margin: 0 }}>
          <legend className="visually-hidden">When do you need this?</legend>
          <div className="row row--tight label" aria-hidden="true">
            <Icon name="calendar" size={16} />
            When do you need this?
          </div>
          <div className="choice-grid" style={{ marginTop: 10 }}>
            {(["Today", "This week"] as const).map((option) => (
              <button
                key={option}
                type="button"
                className="choice"
                aria-pressed={timing === option}
                onClick={() => setTiming(option)}
              >
                {option}
              </button>
            ))}
            <button
              type="button"
              className="choice"
              aria-pressed={timing === "date"}
              onClick={() => setTiming("date")}
            >
              Pick a date
            </button>
          </div>
          {timing === "date" && (
            <input
              type="date"
              className="input"
              style={{ marginTop: 10, height: 46 }}
              aria-label="Date needed"
              value={date}
              min={new Date().toISOString().slice(0, 10)}
              onChange={(event) => setDate(event.target.value)}
            />
          )}
        </fieldset>

        <div className="card card--compact row" style={{ gap: 14 }}>
          <label htmlFor="pj-budget" className="grow">
            <div className="label">Your budget (optional)</div>
            <div className="meta" style={{ marginTop: 2 }}>
              Workers can still suggest a price
            </div>
          </label>
          <div className="input--affix input--money" style={{ height: 44, width: 110 }}>
            <span className="input__prefix">US$</span>
            <input
              id="pj-budget"
              inputMode="decimal"
              value={budget}
              placeholder="—"
              onChange={(event) => setBudget(event.target.value.replace(/[^\d.]/g, ""))}
            />
          </div>
        </div>

        {(formError ?? createJob.error?.message) && (
          <p className="field-error" role="alert">
            {formError ?? createJob.error?.message}
          </p>
        )}

        <div className="spacer" />
        {hasPhotoFailed && (
          <button
            type="button"
            className="btn btn--ghost"
            disabled={isUploading}
            onClick={() => void submit(true)}
          >
            Post without the photo
          </button>
        )}
        <button
          type="submit"
          className="btn btn--primary btn--cta"
          disabled={isUploading || (createJob.isPending && !createJob.isPaused)}
        >
          {isUploading
            ? "Sending photo…"
            : createJob.isPending && !createJob.isPaused
              ? "Posting…"
              : "Find someone for this job"}
          <Icon name="arrowRight" size={18} strokeWidth={2.2} />
        </button>
      </form>

      {isPickerOpen && (
        <TradePickerSheet
          isOpen
          selectedId={skill?.id ?? null}
          onClose={() => setIsPickerOpen(false)}
          onSelect={setSkill}
        />
      )}
      {isLocationOpen && (
        <LocationSheet
          isOpen
          value={location}
          onClose={() => setIsLocationOpen(false)}
          onSave={setLocation}
        />
      )}
    </Screen>
  );
}
