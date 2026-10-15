"use client";

import { Icon } from "@/components/ui/Icon";
import type { SignInRole } from "@/core/session/SessionProvider";

type Props = {
  /** What the person picked ("I need work done" / "I'm looking for work"). */
  chosen: SignInRole;
  /** What their number is actually registered as. */
  registeredAs: SignInRole;
  onContinue: () => void;
  onUseAnotherNumber: () => void;
};

const SIDE: Record<SignInRole, { noun: string; doing: string }> = {
  BUYER: { noun: "someone hiring", doing: "hire people" },
  WORKER: { noun: "a worker", doing: "find work" },
};

/**
 * One number holds one role until the backend lets an account do both
 * (issue #9). Silently opening the other side looked like a broken app,
 * so this says what happened and offers the two ways forward.
 */
export function RoleMismatchNotice({
  chosen,
  registeredAs,
  onContinue,
  onUseAnotherNumber,
}: Props) {
  return (
    <div
      className="stack"
      style={{ flex: 1, gap: 0 }}
      role="alertdialog"
      aria-labelledby="rm-title"
    >
      <div
        className="icon-tile icon-tile--lg icon-tile--amber icon-tile--edged"
        style={{ marginTop: 32 }}
      >
        <Icon name="phone" size={22} />
      </div>
      <h1 id="rm-title" className="title title--display" style={{ marginTop: 20 }}>
        This number is registered as {SIDE[registeredAs].noun}
      </h1>
      <p className="lead" style={{ marginTop: 10 }}>
        You chose to {SIDE[chosen].doing}, but this phone number signed up to{" "}
        {SIDE[registeredAs].doing}. Soon one number will be able to do both. For now, carry on as{" "}
        {SIDE[registeredAs].noun}, or use another number to {SIDE[chosen].doing}.
      </p>
      <div className="spacer" style={{ minHeight: 32 }} />
      <button type="button" className="btn btn--primary btn--cta" onClick={onContinue}>
        Continue as {SIDE[registeredAs].noun}
        <Icon name="arrowRight" size={18} strokeWidth={2.2} />
      </button>
      <button
        type="button"
        className="btn btn--ghost"
        style={{ marginTop: 8 }}
        onClick={onUseAnotherNumber}
      >
        Use another number to {SIDE[chosen].doing}
      </button>
    </div>
  );
}
