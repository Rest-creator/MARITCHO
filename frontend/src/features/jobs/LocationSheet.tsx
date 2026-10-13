"use client";

import { useState } from "react";

import { Sheet } from "@/components/ui/Sheet";
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
 * "Where is the job?" — suburb from the backend's known list (matching
 * depends on it), then the street address, which stays hidden from
 * workers until one is hired.
 */
export function LocationSheet({ isOpen, value, onClose, onSave }: Props) {
  const suburbs = useSuburbs();
  const [draft, setDraft] = useState<JobLocation>(value);
  const canSave = draft.suburb !== "" && draft.address.trim() !== "";

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
          onClick={() => {
            onSave({ ...draft, address: draft.address.trim(), landmark: draft.landmark.trim() });
            onClose();
          }}
        >
          Use this place
        </button>
      }
    >
      <div className="field">
        <label htmlFor="loc-suburb" className="field__label">
          Suburb
        </label>
        <select
          id="loc-suburb"
          className="input"
          value={draft.suburb}
          onChange={(event) => setDraft({ ...draft, suburb: event.target.value })}
        >
          <option value="">{suburbs.isPending ? "Loading suburbs…" : "Choose your suburb"}</option>
          {(suburbs.data ?? []).map((suburb) => (
            <option key={suburb.name} value={suburb.name}>
              {suburb.name}
            </option>
          ))}
        </select>
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
