"use client";

import { useRef, useState, type KeyboardEvent } from "react";

import { Icon } from "@/components/ui/Icon";
import { Sheet } from "@/components/ui/Sheet";
import {
  findNearestSuburb,
  matchSuburbs,
  mergeSuburbs,
  predictSuburb,
} from "@/core/format/suburbs";
import { useSuburbs } from "@/features/workers/hooks";

export interface JobLocation {
  suburb: string;
  address: string;
  landmark: string;
  latitude?: number | null;
  longitude?: number | null;
}

type Props = {
  isOpen: boolean;
  value: JobLocation;
  onClose: () => void;
  onSave: (location: JobLocation) => void;
};

/**
 * "Where is the job?" — suburb combobox (dropdown pick, free write-in typing
 * with live close-match autofill predictions, and one-tap device GPS location),
 * plus the street address, which stays hidden from workers until one is hired.
 */
export function LocationSheet({ isOpen, value, onClose, onSave }: Props) {
  const suburbs = useSuburbs();
  const suburbInputRef = useRef<HTMLInputElement | null>(null);
  const [draft, setDraft] = useState<JobLocation>(value);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isFiltering, setIsFiltering] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const [isLocating, setIsLocating] = useState(false);
  const [locationStatus, setLocationStatus] = useState<string | null>(null);
  const [locationError, setLocationError] = useState<string | null>(null);

  const allSuburbs = mergeSuburbs(suburbs.data);
  const query = isFiltering ? draft.suburb : "";
  const matches = matchSuburbs(query, allSuburbs);
  const prediction = draft.suburb.trim() !== "" ? predictSuburb(draft.suburb, allSuburbs) : null;
  const hasExactMatch = allSuburbs.some(
    (item) => item.toLowerCase() === draft.suburb.trim().toLowerCase(),
  );
  const hasGpsPin =
    typeof draft.latitude === "number" &&
    Number.isFinite(draft.latitude) &&
    typeof draft.longitude === "number" &&
    Number.isFinite(draft.longitude);
  const canSave = draft.suburb.trim() !== "" && (draft.address.trim() !== "" || hasGpsPin);

  function selectSuburb(suburbName: string): void {
    setDraft((current) => ({ ...current, suburb: suburbName }));
    setIsFiltering(false);
    setIsDropdownOpen(false);
    setActiveIndex(0);
    setLocationError(null);
  }

  function handleStartTypingSuburb(): void {
    setDraft((current) => ({
      ...current,
      suburb: "",
      latitude: null,
      longitude: null,
    }));
    setIsFiltering(true);
    setIsDropdownOpen(true);
    setActiveIndex(0);
    setLocationStatus(null);
    setLocationError(null);
    suburbInputRef.current?.focus();
  }

  function handleUseCurrentLocation(): void {
    if (typeof navigator === "undefined" || !("geolocation" in navigator)) {
      setLocationError(
        "Location isn't available on this device. Type or pick your suburb instead.",
      );
      return;
    }
    setIsLocating(true);
    setLocationError(null);
    setLocationStatus(null);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = Math.round(position.coords.latitude * 1_000_000) / 1_000_000;
        const lon = Math.round(position.coords.longitude * 1_000_000) / 1_000_000;
        const nearest = findNearestSuburb(lat, lon, suburbs.data);
        setDraft((current) => ({
          ...current,
          suburb: nearest.suburb,
          latitude: lat,
          longitude: lon,
        }));
        setIsLocating(false);
        setIsFiltering(false);
        setIsDropdownOpen(false);
        setActiveIndex(0);
        setLocationStatus(
          `GPS pin attached · Nearest suburb: ${nearest.suburb} (${nearest.distanceKm} km)`,
        );
      },
      () => {
        setIsLocating(false);
        setLocationError(
          "Could not get your location. Check location permission or type your suburb.",
        );
      },
      { enableHighAccuracy: true, timeout: 10_000, maximumAge: 60_000 },
    );
  }

  function handleSuburbKeyDown(event: KeyboardEvent<HTMLInputElement>): void {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setIsDropdownOpen(true);
      if (matches.length > 0) {
        setActiveIndex((current) => (current + 1) % matches.length);
      }
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      setIsDropdownOpen(true);
      if (matches.length > 0) {
        setActiveIndex((current) => (current - 1 + matches.length) % matches.length);
      }
      return;
    }
    if (
      (event.key === "Enter" || event.key === "Tab") &&
      isDropdownOpen &&
      draft.suburb.trim() !== ""
    ) {
      const target = matches[activeIndex] ?? prediction;
      if (target !== undefined && target !== null && target !== draft.suburb) {
        event.preventDefault();
        selectSuburb(target);
      }
    }
  }

  function handleSave(): void {
    const trimmedSuburb = draft.suburb.trim();
    const canonical =
      allSuburbs.find((item) => item.toLowerCase() === trimmedSuburb.toLowerCase()) ??
      trimmedSuburb;
    const trimmedAddress = draft.address.trim();
    const effectiveAddress =
      trimmedAddress !== "" ? trimmedAddress : hasGpsPin ? `Pinned location (${canonical})` : "";
    onSave({
      suburb: canonical,
      address: effectiveAddress,
      landmark: draft.landmark.trim(),
      ...(hasGpsPin ? { latitude: draft.latitude, longitude: draft.longitude } : {}),
    });
    onClose();
  }

  const showAutofill =
    prediction !== null && prediction.toLowerCase() !== draft.suburb.trim().toLowerCase();

  return (
    <Sheet
      title="Where is the job?"
      isOpen={isOpen}
      onClose={onClose}
      isFitContent
      footer={
        <button
          type="button"
          className="btn btn--primary btn--cta"
          disabled={!canSave}
          onClick={handleSave}
        >
          Use this place
        </button>
      }
    >
      <div className="field">
        <div className="row row--between row--baseline">
          <label htmlFor="loc-suburb" className="field__label">
            Suburb
          </label>
          <button
            type="button"
            className="text-link row row--tight"
            style={{ fontSize: 13 }}
            disabled={isLocating}
            onClick={handleUseCurrentLocation}
          >
            <Icon name="pin" size={14} />
            {isLocating ? "Finding location…" : "Use my location"}
          </button>
        </div>
        <div className="combobox">
          <div className="combobox__control">
            <input
              ref={suburbInputRef}
              id="loc-suburb"
              type="text"
              role="combobox"
              aria-expanded={isDropdownOpen}
              aria-autocomplete="list"
              aria-controls="loc-suburb-listbox"
              className="input combobox__input"
              placeholder={
                suburbs.isPending ? "Loading suburbs…" : "Choose or write in your suburb"
              }
              value={draft.suburb}
              maxLength={100}
              onFocus={() => {
                setIsDropdownOpen(true);
                setIsFiltering(false);
              }}
              onChange={(event) => {
                setDraft({ ...draft, suburb: event.target.value });
                setIsFiltering(true);
                setIsDropdownOpen(true);
                setActiveIndex(0);
              }}
              onKeyDown={handleSuburbKeyDown}
            />
            {showAutofill && prediction !== null ? (
              <button
                type="button"
                className="combobox__autofill"
                title={`Autofill ${prediction}`}
                onClick={() => selectSuburb(prediction)}
              >
                {prediction}
              </button>
            ) : (
              draft.suburb !== "" && (
                <button
                  type="button"
                  className="combobox__toggle"
                  style={{ right: 44 }}
                  aria-label="Clear suburb to type another"
                  title="Clear to type another suburb"
                  onClick={handleStartTypingSuburb}
                >
                  <Icon name="close" size={15} />
                </button>
              )
            )}
            <button
              type="button"
              className="combobox__toggle"
              aria-label={isDropdownOpen ? "Hide the list" : "Show the list"}
              onClick={() => {
                setIsFiltering(false);
                setIsDropdownOpen((open) => !open);
              }}
            >
              <Icon name="chevronDown" size={18} />
            </button>
          </div>

          {isDropdownOpen && (
            <ul
              id="loc-suburb-listbox"
              role="listbox"
              aria-label="Suburb options"
              className="combobox__menu"
            >
              <li role="option" aria-selected={false}>
                <button
                  type="button"
                  className="combobox__option"
                  disabled={isLocating}
                  onClick={handleUseCurrentLocation}
                >
                  <span className="row row--tight">
                    <Icon name="pin" size={16} />
                    <span>
                      {isLocating ? "Finding your current location…" : "Use my current location"}
                    </span>
                  </span>
                  <span className="combobox__badge">GPS</span>
                </button>
              </li>
              {matches.map((suburbName, index) => {
                const isSelected = suburbName.toLowerCase() === draft.suburb.trim().toLowerCase();
                const isClosest =
                  isFiltering && draft.suburb.trim() !== "" && index === activeIndex;
                return (
                  <li key={suburbName} role="option" aria-selected={isSelected || isClosest}>
                    <button
                      type="button"
                      className={
                        isSelected || isClosest
                          ? "combobox__option combobox__option--active"
                          : "combobox__option"
                      }
                      onClick={() => selectSuburb(suburbName)}
                    >
                      <span>{suburbName}</span>
                      {isSelected ? (
                        <span className="combobox__badge">Selected</span>
                      ) : isClosest ? (
                        <span className="combobox__badge">Closest match</span>
                      ) : null}
                    </button>
                  </li>
                );
              })}
              {draft.suburb.trim() !== "" && !hasExactMatch ? (
                <li role="option" aria-selected={matches.length === 0}>
                  <button
                    type="button"
                    className="combobox__option"
                    onClick={() => selectSuburb(draft.suburb.trim())}
                  >
                    <span>Use “{draft.suburb.trim()}”</span>
                    <span className="combobox__badge">Write-in</span>
                  </button>
                </li>
              ) : (
                <li role="option" aria-selected={false}>
                  <button
                    type="button"
                    className="combobox__option"
                    onClick={handleStartTypingSuburb}
                  >
                    <span>Type another suburb…</span>
                    <span className="combobox__badge">Write-in</span>
                  </button>
                </li>
              )}
            </ul>
          )}
        </div>
        {locationStatus && (
          <p className="meta text-emerald" role="status">
            {locationStatus}
          </p>
        )}
        {locationError && (
          <p className="field-error" role="alert">
            {locationError}
          </p>
        )}
        {suburbs.isError && !suburbs.data && <p className="field-error">{suburbs.error.message}</p>}
      </div>
      <div className="field">
        <label htmlFor="loc-address" className="field__label">
          Street address
        </label>
        <input
          id="loc-address"
          className="input"
          autoComplete="street-address"
          placeholder={
            hasGpsPin
              ? "Optional when GPS pin is attached (e.g. 14 Harrow Rd)"
              : "e.g. 14 Harrow Rd"
          }
          value={draft.address}
          maxLength={500}
          onChange={(event) => setDraft({ ...draft, address: event.target.value })}
        />
      </div>
      <div className="field">
        <label htmlFor="loc-landmark" className="field__label">
          How to find it (optional)
        </label>
        <input
          id="loc-landmark"
          className="input"
          placeholder="e.g. Blue gate opposite the church"
          value={draft.landmark}
          maxLength={500}
          onChange={(event) => setDraft({ ...draft, landmark: event.target.value })}
        />
      </div>
      <p className="meta">Only the person you hire sees the street address.</p>
    </Sheet>
  );
}
