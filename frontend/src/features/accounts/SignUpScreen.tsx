"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { BackButton } from "@/components/ui/BackButton";
import { Icon } from "@/components/ui/Icon";
import { Screen } from "@/components/ui/Screen";
import { formatLocalPhone, toInternationalPhone } from "@/core/format/format";
import { updateProfile, useLocalProfile } from "@/core/session/profile-store";
import { requestSignInCode } from "@/core/session/sign-in-code";
import { homeFor, useSession, type SignInRole } from "@/core/session/SessionProvider";
import { RoleMismatchNotice } from "@/features/accounts/RoleMismatchNotice";
import { SignInCodeStep } from "@/features/accounts/SignInCodeStep";

type Props = {
  initialRole: SignInRole;
  isLogin: boolean;
  isExpired: boolean;
};

const LOCAL_PHONE_PATTERN = /^0?\d{9}$/;

export function validateSignUp(name: string, localPhone: string, isLogin: boolean): string | null {
  if (!isLogin && name.trim().length < 2)
    return "Tell us your name so people know who they're dealing with.";
  if (!LOCAL_PHONE_PATTERN.test(localPhone.replace(/\s/g, ""))) {
    return "Enter your mobile number, e.g. 77 412 3089.";
  }
  return null;
}

/** A code was sent; waiting for the person to type it in. */
interface CodeStep {
  phone: string;
  resendAfterSeconds: number;
}

/**
 * Design 2 · Sign up with phone number, then the 6-digit code (2b).
 *
 * The code step only appears when the backend actually sent a code
 * (BACK-009, issue #5). Until it can, sign-in goes straight through the
 * `/token` development mock: showing "code sent" when nothing was sent
 * would mislead.
 */
export function SignUpScreen({ initialRole, isLogin, isExpired }: Props) {
  const router = useRouter();
  const profile = useLocalProfile();
  const { signIn, signOut, isSigningIn, signInError } = useSession();
  const [role, setRole] = useState<SignInRole>(initialRole);
  const [name, setName] = useState(profile.name);
  const [phone, setPhone] = useState(profile.phone === "" ? "" : formatLocalPhone(profile.phone));
  const [validationError, setValidationError] = useState<string | null>(null);
  const [requestError, setRequestError] = useState<string | null>(null);
  const [isRequestingCode, setIsRequestingCode] = useState(false);
  const [codeStep, setCodeStep] = useState<CodeStep | null>(null);
  /** Set when the number is registered as the other role (issue #9). */
  const [registeredAs, setRegisteredAs] = useState<SignInRole | null>(null);

  const isWorker = role === "WORKER";
  const error = validationError ?? requestError ?? signInError;
  const isBusy = isSigningIn || isRequestingCode;

  async function completeSignIn(international: string, code?: string): Promise<void> {
    try {
      const user = await signIn({ phone: international, role, ...(code ? { code } : {}) });
      updateProfile({ phone: international, ...(name.trim() === "" ? {} : { name: name.trim() }) });
      if ((user.role === "BUYER" || user.role === "WORKER") && user.role !== role) {
        setCodeStep(null);
        setRegisteredAs(user.role);
        return;
      }
      router.replace(user.role === "WORKER" && !isLogin ? "/worker/skills" : homeFor(user.role));
    } catch {
      // signInError carries the message.
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const problem = validateSignUp(name, phone, isLogin);
    setValidationError(problem);
    setRequestError(null);
    if (problem !== null) return;

    const international = toInternationalPhone(phone);
    setIsRequestingCode(true);
    try {
      const request = await requestSignInCode(international);
      if (request.isCodeRequired) {
        setCodeStep({ phone: international, resendAfterSeconds: request.resendAfterSeconds });
        return;
      }
    } catch (failure: unknown) {
      setRequestError(failure instanceof Error ? failure.message : "Could not send a code.");
      return;
    } finally {
      setIsRequestingCode(false);
    }
    await completeSignIn(international);
  }

  async function handleResend(): Promise<number> {
    if (codeStep === null) return 0;
    const request = await requestSignInCode(codeStep.phone);
    return request.isCodeRequired ? request.resendAfterSeconds : 0;
  }

  if (registeredAs !== null) {
    return (
      <Screen glow={registeredAs === "WORKER" ? "worker" : "employer"}>
        <RoleMismatchNotice
          chosen={role}
          registeredAs={registeredAs}
          onContinue={() => router.replace(homeFor(registeredAs))}
          onUseAnotherNumber={() => {
            setRegisteredAs(null);
            setPhone("");
            void signOut(`/signup?role=${role === "WORKER" ? "worker" : "buyer"}`);
          }}
        />
      </Screen>
    );
  }

  if (codeStep !== null) {
    return (
      <Screen glow={isWorker ? "worker" : "employer"}>
        <SignInCodeStep
          phone={codeStep.phone}
          resendAfterSeconds={codeStep.resendAfterSeconds}
          isVerifying={isSigningIn}
          error={signInError}
          onVerify={(code) => void completeSignIn(codeStep.phone, code)}
          onResend={handleResend}
          onChangeNumber={() => setCodeStep(null)}
        />
      </Screen>
    );
  }

  return (
    <Screen glow={isWorker ? "worker" : "employer"}>
      <form onSubmit={handleSubmit} className="stack" style={{ flex: 1, gap: 0 }} noValidate>
        <div className="topbar topbar--split">
          <BackButton fallbackHref="/" />
          {isWorker && !isLogin && (
            <div className="label" style={{ fontSize: 13 }}>
              Step 1 of 2
            </div>
          )}
        </div>
        {isWorker && !isLogin && (
          <div className="progress" style={{ marginTop: 12 }}>
            <div className="progress__fill" style={{ width: "50%" }} />
          </div>
        )}

        {isExpired && (
          <div className="banner banner--amber" style={{ marginTop: 20 }} role="status">
            Your session ended. Sign in again to carry on — nothing you saved is lost.
          </div>
        )}

        <h1 className="title title--display" style={{ marginTop: 32 }}>
          {isLogin ? "Welcome back" : "Let's get you set up"}
        </h1>
        <p className="lead" style={{ marginTop: 10 }}>
          {isLogin
            ? "Sign in with the phone number you used before."
            : "Just your name and phone number — no email needed."}
        </p>

        {isLogin && (
          <div
            className="segmented segmented--choice"
            style={{ marginTop: 24 }}
            role="group"
            aria-label="I am"
          >
            <button
              type="button"
              className="segmented__tab"
              aria-pressed={role === "BUYER"}
              onClick={() => setRole("BUYER")}
            >
              I need work done
            </button>
            <button
              type="button"
              className="segmented__tab"
              aria-pressed={role === "WORKER"}
              onClick={() => setRole("WORKER")}
            >
              I find work
            </button>
          </div>
        )}

        {!isLogin && (
          <div className="field" style={{ marginTop: 28 }}>
            <label htmlFor="su-name" className="field__label">
              Your name
            </label>
            <input
              id="su-name"
              className="input"
              type="text"
              autoComplete="name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              maxLength={80}
            />
          </div>
        )}

        <div className="field" style={{ marginTop: 18 }}>
          <label htmlFor="su-phone" className="field__label">
            Phone number
          </label>
          <div className="row" style={{ gap: 8 }}>
            <div
              className="input"
              style={{
                width: "auto",
                display: "flex",
                alignItems: "center",
                gap: 6,
                padding: "0 14px",
                fontWeight: 600,
              }}
              aria-label="Country code Zimbabwe +263"
            >
              +263
              <Icon name="chevronDown" size={16} strokeWidth={2} />
            </div>
            <input
              id="su-phone"
              className="input"
              type="tel"
              inputMode="tel"
              autoComplete="tel-national"
              placeholder="77 412 3089"
              value={phone}
              onChange={(event) => setPhone(event.target.value)}
              aria-invalid={validationError !== null}
              aria-describedby={error ? "su-error" : undefined}
              style={{ flex: 1, minWidth: 0 }}
            />
          </div>
        </div>

        {error && (
          <p id="su-error" className="field-error" role="alert" style={{ marginTop: 12 }}>
            {error}
          </p>
        )}

        <div className="spacer" style={{ minHeight: 32 }} />

        <button type="submit" className="btn btn--primary btn--cta" disabled={isBusy}>
          {isRequestingCode ? "Sending your code…" : isSigningIn ? "Signing you in…" : "Continue"}
          {!isBusy && <Icon name="arrowRight" size={18} strokeWidth={2.2} />}
        </button>
        <p className="meta" style={{ marginTop: 14, textAlign: "center", lineHeight: 1.5 }}>
          By continuing you agree to our{" "}
          <Link
            href="/terms"
            style={{ color: "var(--text-secondary)", textDecoration: "underline" }}
          >
            Terms
          </Link>{" "}
          and{" "}
          <Link
            href="/privacy"
            style={{ color: "var(--text-secondary)", textDecoration: "underline" }}
          >
            Privacy Policy
          </Link>
        </p>
      </form>
    </Screen>
  );
}
