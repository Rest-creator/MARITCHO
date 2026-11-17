"use client";

import { useState, type KeyboardEvent } from "react";

import { Icon } from "@/components/ui/Icon";
import { Sheet } from "@/components/ui/Sheet";
import { matchSuburbs, mergeSuburbs, predictSuburb } from "@/core/format/suburbs";
import { useSuburbs } from "@/features/workers/hooks";

export interface JobLocation {
  suburb: string;
  address: string;
  landmark: string;
}

type Props = {
  isOpen: boolean;
  value: JobLocation;
  onClose: () => void;
  onSave: (location: JobLocation) => void;
};

/**
 * "Where is the job?" — suburb combobox (both a dropdown pick and a write-in
 * with live close-match autofill predictions as you type), plus the street
 * address, which stays hidden from workers until one is hired.
 */
export function LocationSheet({ isOpen, value, onClose, onSave }: Props) {
  const suburbs = useSuburbs();
  const [draft, setDraft] = useState<JobLocation>(value);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isFiltering, setIsFiltering] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);

  const allSuburbs = mergeSuburbs(suburbs.data);
  const query = isFiltering ? draft.suburb : "";
  const matches = matchSuburbs(query, allSuburbs);
  const prediction = draft.suburb.trim() !== "" ? predictSuburb(draft.suburb, allSuburbs) : null;
  const hasExactMatch = allSuburbs.some(
    (item) => item.toLowerCase() === draft.suburb.trim().toLowerCase(),
  );
  const canSave = draft.suburb.trim() !== "" && draft.address.trim() !== "";

  function selectSuburb(suburbName: string): void {
    setDraft((current) => ({ ...current, suburb: suburbName }));
    setIsFiltering(false);
    setIsDropdownOpen(false);
    setActiveIndex(0);
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
    onSave({
      suburb: canonical,
      address: draft.address.trim(),
      landmark: draft.landmark.trim(),
    });
    onClose();
  }

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
        <label htmlFor="loc-suburb" className="field__label">
          Suburb
        </label>
        <div className="combobox">
          <div className="combobox__control">
            <input
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
            {prediction !== null &&
              prediction.toLowerCase() !== draft.suburb.trim().toLowerCase() && (
                <button
                  type="button"
                  className="combobox__autofill"
                  title={`Autofill ${prediction}`}
                  onClick={() => selectSuburb(prediction)}
                >
                  {prediction}
                </button>
              )}
            <button
              type="button"
              className="combobox__toggle"
              aria-label={isDropdownOpen ? "Hide suburb options" : "Show suburb options"}
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
              {draft.suburb.trim() !== "" && !hasExactMatch && (
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
              )}
            </ul>
          )}
        </div>
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
          placeholder="e.g. 14 Harrow Rd"
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
