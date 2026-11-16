"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { BackButton } from "@/components/ui/BackButton";
import { Icon } from "@/components/ui/Icon";
import { Screen } from "@/components/ui/Screen";
import { formatLocalPhone, toInternationalPhone } from "@/core/format/format";
import { updateProfile, useLocalProfile } from "@/core/session/profile-store";
import { homeFor, useSession, type SignInRole } from "@/core/session/SessionProvider";
import { RoleMismatchNotice } from "@/features/accounts/RoleMismatchNotice";
import { useUpdateUserProfile } from "@/features/workers/hooks";

type Props = {
  initialRole: SignInRole;
  isLogin: boolean;
  isExpired: boolean;
};

const LOCAL_PHONE_PATTERN = /^0?\d{9}$/;

export function validateSignUp(
  name: string,
  localPhone: string,
  password: string,
  isLogin: boolean,
): string | null {
  if (!isLogin && name.trim().length < 2)
    return "Tell us your name so people know who they're dealing with.";
  if (!LOCAL_PHONE_PATTERN.test(localPhone.replace(/\s/g, ""))) {
    return "Enter your mobile number, e.g. 77 412 3089.";
  }
  if (password.length < 8) {
    return "Use a password with at least 8 characters.";
  }
  return null;
}

/** Design 2 · Sign up or sign in with phone number and password. */
export function SignUpScreen({ initialRole, isLogin, isExpired }: Props) {
  const router = useRouter();
  const profile = useLocalProfile();
  const { signUp, signIn, signOut, isSigningIn, signInError } = useSession();
  const updateServerProfile = useUpdateUserProfile();
  const [role, setRole] = useState<SignInRole>(initialRole);
  const [name, setName] = useState(profile.name);
  const [phone, setPhone] = useState(profile.phone === "" ? "" : formatLocalPhone(profile.phone));
  const [password, setPassword] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);
  /** Set when the number is registered as the other role (issue #9). */
  const [registeredAs, setRegisteredAs] = useState<SignInRole | null>(null);

  const isWorker = role === "WORKER";
  const error = validationError ?? signInError;

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const problem = validateSignUp(name, phone, password, isLogin);
    setValidationError(problem);
    if (problem !== null) return;

    const international = toInternationalPhone(phone);
    const trimmedName = name.trim();
    try {
      const user = isLogin
        ? await signIn({ phone: international, password })
        : await signUp({ phone: international, password, name: trimmedName, role });
      updateProfile({ phone: international, ...(trimmedName === "" ? {} : { name: trimmedName }) });
      if ((user.role === "BUYER" || user.role === "WORKER") && user.role !== role) {
        setRegisteredAs(user.role);
        return;
      }
      if (trimmedName !== "") {
        updateServerProfile.mutate({ display_name: trimmedName });
      }
      router.replace(user.role === "WORKER" && !isLogin ? "/worker/skills" : homeFor(user.role));
    } catch {
      // signInError carries the message.
    }
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
            ? "Sign in with your phone number and password."
            : "Your name, phone number and a password — no email needed."}
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

        <div className="field" style={{ marginTop: 18 }}>
          <label htmlFor="su-password" className="field__label">
            Password
          </label>
          <input
            id="su-password"
            className="input"
            type="password"
            autoComplete={isLogin ? "current-password" : "new-password"}
            placeholder="At least 8 characters"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            aria-invalid={validationError !== null}
            aria-describedby={error ? "su-error" : undefined}
          />
        </div>

        {error && (
          <p id="su-error" className="field-error" role="alert" style={{ marginTop: 12 }}>
            {error}
          </p>
        )}

        <div className="spacer" style={{ minHeight: 32 }} />

        <button type="submit" className="btn btn--primary btn--cta" disabled={isSigningIn}>
          {isSigningIn ? (isLogin ? "Signing you in…" : "Creating your account…") : "Continue"}
          {!isSigningIn && <Icon name="arrowRight" size={18} strokeWidth={2.2} />}
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
