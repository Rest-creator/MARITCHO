"use client";

import { useState } from "react";

import { Sheet } from "@/components/ui/Sheet";
import { useDisputes, useRespondToDispute } from "@/features/jobs/hooks";

type Props = { jobId: string; onClose: () => void };

/** The worker's side of a dispute — always heard before any consequence. */
export function RespondSheet({ jobId, onClose }: Props) {
  const disputes = useDisputes(jobId, true);
  const respond = useRespondToDispute();
  const [response, setResponse] = useState("");
  const open = disputes.data?.find((dispute) => dispute.worker_response === null);

  return (
    <Sheet
      title="The client raised a concern"
      isOpen
      onClose={onClose}
      isFitContent
      footer={
        <button
          type="button"
          className="btn btn--primary btn--cta"
          disabled={response.trim().length < 5 || respond.isPending}
          onClick={() =>
            respond.mutate({ jobId, response: response.trim() }, { onSuccess: onClose })
          }
        >
          {respond.isPending ? "Sending…" : "Send my answer"}
        </button>
      }
    >
      <div className="card card--quiet">
        <div className="label">What they said</div>
        <p style={{ marginTop: 6, fontSize: 14, lineHeight: 1.5 }}>
          {disputes.isPending ? "Loading…" : (open?.reason ?? "No open concern found.")}
        </p>
      </div>
      <p className="meta meta--secondary" style={{ lineHeight: 1.5 }}>
        Your standing is paused, not lowered, while this is open. Most concerns are settled with a
        return visit.
      </p>
      <div className="field">
        <label htmlFor="respond-text" className="field__label">
          Your answer
        </label>
        <textarea
          id="respond-text"
          rows={4}
          className="textarea"
          maxLength={2000}
          placeholder="e.g. I'll come back tomorrow at 9am to reseal the joint."
          value={response}
          onChange={(event) => setResponse(event.target.value)}
        />
      </div>
      {respond.error && (
        <p className="field-error" role="alert">
          {respond.error.message}
        </p>
      )}
    </Sheet>
  );
}
