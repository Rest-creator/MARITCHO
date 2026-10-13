"use client";

import { useState } from "react";

import { Sheet } from "@/components/ui/Sheet";
import type { Job } from "@/core/api/schemas";
import { formatMoney } from "@/core/format/format";
import { useSubmitQuote } from "@/features/jobs/hooks";
import { parseOfferAmount } from "@/features/worker/money-input";

type Props = { job: Job; offeredAmount: number | null; onClose: () => void };

/**
 * "I've arrived" — the worker confirms the real price after seeing the job.
 * The backend requires the total to exceed the deposit already held.
 */
export function QuoteSheet({ job, offeredAmount, onClose }: Props) {
  const submitQuote = useSubmitQuote();
  const [labour, setLabour] = useState(offeredAmount === null ? "" : String(offeredAmount));
  const [materials, setMaterials] = useState("0");
  const labourAmount = parseOfferAmount(labour);
  const materialsAmount = materials === "" ? 0 : Number(materials);
  const total = (labourAmount ?? 0) + (Number.isFinite(materialsAmount) ? materialsAmount : 0);
  const isValid = labourAmount !== null && Number.isFinite(materialsAmount) && materialsAmount >= 0;

  return (
    <Sheet
      title="Confirm the price"
      isOpen
      onClose={onClose}
      isFitContent
      footer={
        <button
          type="button"
          className="btn btn--primary btn--cta"
          disabled={!isValid || submitQuote.isPending}
          onClick={() =>
            labourAmount !== null &&
            submitQuote.mutate(
              { jobId: job.id, labor_amount: labourAmount, materials_amount: materialsAmount },
              { onSuccess: onClose },
            )
          }
        >
          {submitQuote.isPending ? "Sending…" : `Send price · ${formatMoney(total)}`}
        </button>
      }
    >
      <p className="meta meta--secondary" style={{ lineHeight: 1.5 }}>
        Now that you&apos;ve seen the job, confirm what it will cost. The client sees it straight
        away and pays it when they sign the job off
        {offeredAmount === null ? "" : ` — you offered ${formatMoney(offeredAmount)}`}.
      </p>
      <div className="row" style={{ gap: 8 }}>
        <div className="field grow">
          <label htmlFor="q-labour" className="field__label">
            Your work
          </label>
          <label className="input--affix input--money">
            <span className="input__prefix">$</span>
            <input
              id="q-labour"
              inputMode="decimal"
              value={labour}
              onChange={(event) => setLabour(event.target.value.replace(/[^\d.]/g, ""))}
            />
          </label>
        </div>
        <div className="field grow">
          <label htmlFor="q-materials" className="field__label">
            Materials
          </label>
          <label className="input--affix input--money">
            <span className="input__prefix">$</span>
            <input
              id="q-materials"
              inputMode="decimal"
              value={materials}
              onChange={(event) => setMaterials(event.target.value.replace(/[^\d.]/g, ""))}
            />
          </label>
        </div>
      </div>
      {submitQuote.error && (
        <p className="field-error" role="alert">
          {submitQuote.error.message}
        </p>
      )}
    </Sheet>
  );
}
