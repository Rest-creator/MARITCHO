"use client";

import { useState, type FormEvent } from "react";
import { onlineManager } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { BackButton } from "@/components/ui/BackButton";
import { Icon } from "@/components/ui/Icon";
import { Screen } from "@/components/ui/Screen";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/States";
import { distanceBandLabel, formatKm, formatMoney, formatRelativeTime } from "@/core/format/format";
import { tradeLabel } from "@/core/format/trades";
import { useMyOffers, useOpenJobs, useSubmitOffer } from "@/features/jobs/hooks";
import { splitTiming } from "@/features/jobs/job-helpers";
import { parseOfferAmount } from "@/features/worker/money-input";

type Props = { jobId: string };

/**
 * Design W3 · Job details. Like inDrive: accept the client's price with one
 * tap, or offer a different one; the client then approves one worker.
 */
export function JobDetailScreen({ jobId }: Props) {
  const router = useRouter();
  const openJobs = useOpenJobs();
  const offers = useMyOffers();
  const submitOffer = useSubmitOffer();
  const job = openJobs.data?.find((item) => item.job_id === jobId);
  const existing = offers.data?.find((offer) => offer.job_id === jobId);

  const [price, setPrice] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  /** "Offer a different price" was tapped (or there's no price to accept). */
  const [isCountering, setIsCountering] = useState(false);

  if (openJobs.isPending) {
    return (
      <Screen glow="worker">
        <Skeleton height={56} />
        <Skeleton height={160} count={2} />
      </Screen>
    );
  }

  if (!job) {
    return (
      <Screen glow="worker">
        <div className="topbar">
          <BackButton fallbackHref="/worker" />
        </div>
        {openJobs.isError ? (
          <ErrorState message={openJobs.error.message} onRetry={() => void openJobs.refetch()} />
        ) : (
          <EmptyState title="This job has been filled" icon="briefcase">
            The client may already have hired someone. There are more jobs on your list.
          </EmptyState>
        )}
      </Screen>
    );
  }

  const { text, timing } = splitTiming(job.problem_description);
  const title = text.split("\n")[0] || tradeLabel(job.trade);
  const budget = job.budget_amount;
  const isAccepted = existing !== undefined && budget !== null && existing.quoted_amount === budget;
  const showPriceField = isCountering || budget === null;
  const priceValue = price ?? String(existing?.quoted_amount ?? budget ?? "");
  const noteValue = note ?? existing?.availability_note ?? "";
  const isSending = submitOffer.isPending && !submitOffer.isPaused;

  function send(amount: number): void {
    setError(null);
    const input = {
      jobId,
      quoted_amount: amount,
      ...(noteValue.trim() === "" ? {} : { availability_note: noteValue.trim().slice(0, 255) }),
    };
    if (!onlineManager.isOnline()) {
      submitOffer.mutate(input);
      router.push("/worker/work?tab=offers");
      return;
    }
    submitOffer.mutate(input, { onSuccess: () => router.push("/worker/work?tab=offers") });
  }

  /** "Send my price": the worker's own price. */
  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const amount = parseOfferAmount(priceValue);
    if (amount === null) {
      setError("Enter the price you'd charge, in US dollars.");
      return;
    }
    send(amount);
  }

  return (
    <Screen glow="worker">
      <form onSubmit={handleSubmit} className="stack" style={{ flex: 1, gap: 14 }} noValidate>
        <div className="topbar">
          <BackButton fallbackHref="/worker" />
          <div className="topbar__text">
            <h1 className="title">{title}</h1>
            <div className="meta">
              {tradeLabel(job.trade)} · Posted {formatRelativeTime(job.created_at)}
            </div>
          </div>
        </div>

        <section className="card" style={{ padding: "14px 16px" }}>
          <h2 className="label" style={{ fontSize: 13, fontWeight: 700 }}>
            What the client needs
          </h2>
          <p style={{ marginTop: 6, fontSize: 15, lineHeight: 1.55, whiteSpace: "pre-line" }}>
            {text || "No description given — ask in your offer note."}
          </p>
          <div className="card__divider facts">
            <div>
              <div className="fact__label">Where</div>
              <div className="fact__value">{job.suburb}</div>
              <div className="fact__hint">{formatKm(job.distance_km)}</div>
            </div>
            <div>
              <div className="fact__label">When</div>
              <div className="fact__value">{timing ?? "Flexible"}</div>
              <div className="fact__hint">{distanceBandLabel(job.distance_band)}</div>
            </div>
            <div>
              <div className="fact__label">Budget</div>
              <div className="fact__value">
                {job.budget_amount === null ? "Open" : formatMoney(job.budget_amount)}
              </div>
              <div className="fact__hint">Cash/EcoCash</div>
            </div>
          </div>
        </section>

        <div className="banner banner--quiet" style={{ borderRadius: 16 }}>
          <span className="text-emerald" style={{ display: "flex" }}>
            <Icon name="shieldCheck" size={18} />
          </span>
          The exact address is shared with you once you&apos;re hired. Payment is held by Maricho.
        </div>

        {existing && (
          <div className="banner banner--emerald" role="status">
            <Icon name="check" size={18} />
            {isAccepted
              ? `You accepted ${formatMoney(existing.quoted_amount)}. Waiting for the client to approve.`
              : `You offered ${formatMoney(existing.quoted_amount)}. Waiting for the client to approve.`}
          </div>
        )}

        <label className="input--affix">
          <Icon name="clock" size={18} />
          <input
            aria-label="When you can come"
            placeholder="When can you come? e.g. today at 2pm"
            maxLength={255}
            value={noteValue}
            onChange={(event) => setNote(event.target.value)}
          />
        </label>

        {showPriceField && (
          <section className="card card--amber stack" style={{ padding: "14px 16px" }}>
            <h2 style={{ fontSize: 15, fontWeight: 700 }}>
              {budget === null ? "The client didn't set a price. What's yours?" : "Your price"}
            </h2>
            <label className="input--affix input--money" style={{ width: 140 }}>
              <span className="input__prefix">$</span>
              <input
                inputMode="decimal"
                aria-label="Your price in US dollars"
                value={priceValue}
                onChange={(event) => setPrice(event.target.value.replace(/[^\d.]/g, ""))}
              />
            </label>
            <div className="meta">
              The client sees your price, track record and how close you are.
            </div>
          </section>
        )}

        {(error ?? submitOffer.error?.message) && (
          <p className="field-error" role="alert">
            {error ?? submitOffer.error?.message}
          </p>
        )}
        <div className="spacer" />

        {budget !== null && !showPriceField ? (
          <>
            <button
              type="button"
              className="btn btn--primary btn--cta"
              disabled={isSending || isAccepted}
              onClick={() => send(budget)}
            >
              {isSending
                ? "Sending…"
                : isAccepted
                  ? `Accepted · ${formatMoney(budget)}`
                  : `Accept for ${formatMoney(budget)}`}
              {!isSending && !isAccepted && <Icon name="check" size={18} strokeWidth={2.4} />}
            </button>
            <button type="button" className="btn btn--ghost" onClick={() => setIsCountering(true)}>
              Offer a different price
            </button>
          </>
        ) : (
          <>
            <button type="submit" className="btn btn--primary btn--cta" disabled={isSending}>
              {isSending ? "Sending…" : existing ? "Update my price" : "Send my price"}
              <Icon name="send" size={18} strokeWidth={2.2} />
            </button>
            {budget !== null && (
              <button
                type="button"
                className="btn btn--ghost"
                onClick={() => {
                  setIsCountering(false);
                  setPrice(null);
                }}
              >
                Accept {formatMoney(budget)} instead
              </button>
            )}
          </>
        )}
      </form>
    </Screen>
  );
}
