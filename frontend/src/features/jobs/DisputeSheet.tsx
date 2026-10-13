"use client";

import { useState } from "react";

import { Sheet } from "@/components/ui/Sheet";
import { useRaiseDispute } from "@/features/jobs/hooks";

type Props = { jobId: string; onClose: () => void };

/** "Something's not right" — freezes payment until the worker responds. */
export function DisputeSheet({ jobId, onClose }: Props) {
  const raiseDispute = useRaiseDispute();
  const [reason, setReason] = useState("");
  const canSend = reason.trim().length >= 5;

  return (
    <Sheet
      title="Something's not right"
      isOpen
      onClose={onClose}
      isFitContent
      footer={
        <button
          type="button"
          className="btn btn--primary btn--cta"
          disabled={!canSend || raiseDispute.isPending}
          onClick={() =>
            raiseDispute.mutate({ jobId, reason: reason.trim() }, { onSuccess: onClose })
          }
        >
          {raiseDispute.isPending ? "Sending…" : "Hold payment & tell the worker"}
        </button>
      }
    >
      <p className="meta meta--secondary" style={{ lineHeight: 1.5 }}>
        Payment stays on hold. The worker gets a chance to answer first — usually by coming back to
        fix it. Nobody is penalised before they&apos;ve been heard.
      </p>
      <div className="field">
        <label htmlFor="dispute-reason" className="field__label">
          What&apos;s wrong?
        </label>
        <textarea
          id="dispute-reason"
          rows={4}
          className="textarea"
          maxLength={2000}
          placeholder="e.g. The pipe is still dripping under the sink."
          value={reason}
          onChange={(event) => setReason(event.target.value)}
        />
      </div>
      {raiseDispute.error && (
        <p className="field-error" role="alert">
          {raiseDispute.error.message}
        </p>
      )}
    </Sheet>
  );
}
