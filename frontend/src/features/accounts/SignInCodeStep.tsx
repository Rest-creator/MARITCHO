"use client";

import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from "react";

import { Icon } from "@/components/ui/Icon";
import { formatLocalPhone } from "@/core/format/format";
import { formatCountdown, normaliseCode } from "@/core/session/sign-in-code";

type Props = {
  /** International number the code went to, e.g. +263774123089. */
  phone: string;
  resendAfterSeconds: number;
  isVerifying: boolean;
  error: string | null;
  onVerify: (code: string) => void;
  /** Sends a new code; resolves to the new wait before another can be sent. */
  onResend: () => Promise<number>;
  onChangeNumber: () => void;
};

/**
 * Design 2b · Enter the 6-digit code. One numeric field (not six boxes) so
 * Android can fill it from the SMS and a pasted code just works; it signs
 * in by itself as soon as the sixth digit is in.
 */
export function SignInCodeStep({
  phone,
  resendAfterSeconds,
  isVerifying,
  error,
  onVerify,
  onResend,
  onChangeNumber,
}: Props) {
  const [code, setCode] = useState("");
  const [deadline, setDeadline] = useState(() => Date.now() + resendAfterSeconds * 1000);
  const [now, setNow] = useState(() => Date.now());
  const [isResending, setIsResending] = useState(false);
  const [resendNote, setResendNote] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const secondsLeft = Math.max(0, (deadline - now) / 1000);
  const canResend = secondsLeft === 0 && !isResending;

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    if (deadline <= Date.now()) return;
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [deadline]);

  function handleChange(event: ChangeEvent<HTMLInputElement>): void {
    const next = normaliseCode(event.target.value);
    setCode(next);
    if (next.length === 6 && next !== code && !isVerifying) onVerify(next);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (code.length === 6) onVerify(code);
  }

  async function handleResend(): Promise<void> {
    setIsResending(true);
    setResendNote(null);
    try {
      const wait = await onResend();
      setCode("");
      setDeadline(Date.now() + wait * 1000);
      setNow(Date.now());
      setResendNote("New code sent.");
      inputRef.current?.focus();
    } catch (failure: unknown) {
      setResendNote(failure instanceof Error ? failure.message : "Could not send a new code.");
    } finally {
      setIsResending(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="stack" style={{ flex: 1, gap: 0 }} noValidate>
      <h1 className="title title--display" style={{ marginTop: 32 }}>
        Enter your code
      </h1>
      <p className="lead" style={{ marginTop: 10 }}>
        We sent a 6-digit code to{" "}
        <span className="strong" style={{ whiteSpace: "nowrap" }}>
          +263 {formatLocalPhone(phone)}
        </span>
        .
      </p>

      <div className="field" style={{ marginTop: 28 }}>
        <label htmlFor="su-code" className="field__label">
          6-digit code
        </label>
        <input
          ref={inputRef}
          id="su-code"
          className="input input--code"
          type="text"
          inputMode="numeric"
          autoComplete="one-time-code"
          pattern="\d{6}"
          maxLength={7}
          placeholder="••••••"
          value={code}
          onChange={handleChange}
          aria-invalid={error !== null}
          aria-describedby={error ? "su-code-error" : undefined}
          disabled={isVerifying}
        />
      </div>

      {error && (
        <p id="su-code-error" className="field-error" role="alert" style={{ marginTop: 12 }}>
          {error}
        </p>
      )}

      <div className="row row--between" style={{ marginTop: 18 }}>
        <button type="button" className="text-link" onClick={onChangeNumber}>
          Change number
        </button>
        {canResend ? (
          <button type="button" className="text-link" onClick={() => void handleResend()}>
            Send a new code
          </button>
        ) : (
          <span className="meta" aria-live="polite">
            {isResending ? "Sending…" : `New code in ${formatCountdown(secondsLeft)}`}
          </span>
        )}
      </div>
      {resendNote && (
        <p className="meta" role="status" style={{ marginTop: 8, textAlign: "right" }}>
          {resendNote}
        </p>
      )}

      <div className="spacer" style={{ minHeight: 32 }} />

      <button
        type="submit"
        className="btn btn--primary btn--cta"
        disabled={isVerifying || code.length !== 6}
      >
        {isVerifying ? "Signing you in…" : "Continue"}
        {!isVerifying && <Icon name="arrowRight" size={18} strokeWidth={2.2} />}
      </button>
    </form>
  );
}
