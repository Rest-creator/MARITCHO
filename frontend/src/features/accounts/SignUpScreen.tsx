"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { BackButton } from "@/components/ui/BackButton";
import { Icon } from "@/components/ui/Icon";
import { Screen } from "@/components/ui/Screen";
import { formatLocalPhone, toInternationalPhone } from "@/core/format/format";
import { mergeSuburbs } from "@/core/format/suburbs";
import { TRAVEL_MEANS_OPTIONS } from "@/core/format/travel";
import { updateProfile, useLocalProfile } from "@/core/session/profile-store";
import { homeFor, useSession, type SignInRole } from "@/core/session/SessionProvider";
import { RoleMismatchNotice } from "@/features/accounts/RoleMismatchNotice";
import { useSuburbs, useUpdateUserProfile } from "@/features/workers/hooks";

type Props = {
  initialRole: SignInRole;
  isLogin: boolean;
  isExpired: boolean;
};

const LOCAL_PHONE_PATTERN = /^0?\d{9}$/;

function digitsOnly(value: string): string {
  return value.replace(/\D/g, "").replace(/^0/, "");
}

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

export interface SignUpDetails {
  role: SignInRole;
  suburb: string;
  phone: string;
  emergencyPhone: string;
}

/** Extra checks for a new account, after `validateSignUp` passes. */
export function validateSignUpDetails(details: SignUpDetails): string | null {
  if (details.suburb.trim() === "") {
    return details.role === "WORKER"
      ? "Choose the suburb you're based in so we can show jobs nearby."
      : "Choose the suburb where you usually need work done.";
  }
  const emergency: string = details.emergencyPhone.replace(/\s/g, "");
  if (emergency !== "") {
    if (!LOCAL_PHONE_PATTERN.test(emergency)) {
      return "Enter the emergency contact's mobile number, e.g. 77 200 0111.";
    }
    if (digitsOnly(emergency) === digitsOnly(details.phone)) {
      return "Your emergency contact should be someone else's number.";
    }
  }
  return null;
}

/** Design 2 · Log in, or create an account with a few details about you. */
export function SignUpScreen({ initialRole, isLogin, isExpired }: Props) {
  const router = useRouter();
  const profile = useLocalProfile();
  const { signUp, signIn, signOut, isSigningIn, signInError } = useSession();
  const updateServerProfile = useUpdateUserProfile();
  const suburbsQuery = useSuburbs();
  const suburbOptions: string[] = mergeSuburbs(suburbsQuery.data);

  const [role, setRole] = useState<SignInRole>(initialRole);
  const [name, setName] = useState(profile.name);
  const [phone, setPhone] = useState(profile.phone === "" ? "" : formatLocalPhone(profile.phone));
  const [password, setPassword] = useState("");
  const [suburb, setSuburb] = useState(profile.homeSuburb);
  const [address, setAddress] = useState(profile.lastAddress);
  const [travelMeans, setTravelMeans] = useState(profile.travelMeans);
  const [emergencyPhone, setEmergencyPhone] = useState(
    profile.nextOfKinPhone === "" ? "" : formatLocalPhone(profile.nextOfKinPhone),
  );
  const [validationError, setValidationError] = useState<string | null>(null);
  /** Set when the number is registered as the other role (issue #9). */
  const [registeredAs, setRegisteredAs] = useState<SignInRole | null>(null);

  const isWorker = role === "WORKER";
  const roleParam: string = isWorker ? "worker" : "buyer";
  const error = validationError ?? signInError;

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const problem: string | null =
      validateSignUp(name, phone, password, isLogin) ??
      (isLogin ? null : validateSignUpDetails({ role, suburb, phone, emergencyPhone }));
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
      if (isLogin) {
        if (trimmedName !== "") updateServerProfile.mutate({ display_name: trimmedName });
        router.replace(homeFor(user.role));
        return;
      }
      saveNewAccountDetails(trimmedName);
      router.replace(user.role === "WORKER" ? "/worker/skills" : homeFor(user.role));
    } catch {
      // signInError carries the message.
    }
  }

  /** Keeps the extra sign-up details on this phone and on the account. */
  function saveNewAccountDetails(trimmedName: string): void {
    const cleanSuburb: string = suburb.trim();
    const emergency: string =
      emergencyPhone.trim() === "" ? "" : toInternationalPhone(emergencyPhone);
    updateProfile({
      homeSuburb: cleanSuburb,
      nextOfKinPhone: emergency,
      ...(isWorker ? { travelMeans } : { lastSuburb: cleanSuburb, lastAddress: address.trim() }),
    });
    updateServerProfile.mutate({
      display_name: trimmedName,
      home_suburb: cleanSuburb,
      ...(emergency === "" ? {} : { next_of_kin_phone: emergency }),
    });
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
            void signOut(`/signup?${isLogin ? "mode=login&" : ""}role=${roleParam}`);
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
            ? "Log in with your phone number and password."
            : "A few details so the right people can find you — no email needed."}
        </p>

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

        {!isLogin && (
          <div className="field" style={{ marginTop: 28 }}>
            <label htmlFor="su-name" className="field__label">
              Your full name
            </label>
            <input
              id="su-name"
              className="input"
              type="text"
              autoComplete="name"
              placeholder="e.g. Tariro Moyo"
              value={name}
              onChange={(event) => setName(event.target.value)}
              maxLength={80}
            />
          </div>
        )}

        <div className="field" style={{ marginTop: isLogin ? 28 : 18 }}>
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

        {!isLogin && (
          <>
            <div className="field" style={{ marginTop: 18 }}>
              <label htmlFor="su-suburb" className="field__label">
                {isWorker ? "Where are you based?" : "Where do you usually need work done?"}
              </label>
              <select
                id="su-suburb"
                className="input"
                style={{ height: 48 }}
                value={suburb}
                onChange={(event) => setSuburb(event.target.value)}
              >
                <option value="">Choose your suburb</option>
                {suburbOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
              <span className="meta">
                {isWorker
                  ? "We show you jobs near here first."
                  : "We show you workers near here first."}
              </span>
            </div>

            {isWorker ? (
              <div className="field" style={{ marginTop: 18 }}>
                <span className="field__label" id="su-travel-label">
                  How do you get to jobs?
                </span>
                <div className="chip-list" role="group" aria-labelledby="su-travel-label">
                  {TRAVEL_MEANS_OPTIONS.map((mode) => (
                    <button
                      key={mode}
                      type="button"
                      className={travelMeans === mode ? "tag tag--verified" : "tag"}
                      aria-pressed={travelMeans === mode}
                      onClick={() => setTravelMeans(travelMeans === mode ? "" : mode)}
                    >
                      {mode}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="field" style={{ marginTop: 18 }}>
                <label htmlFor="su-address" className="field__label">
                  House number or street (optional)
                </label>
                <input
                  id="su-address"
                  className="input"
                  type="text"
                  autoComplete="street-address"
                  placeholder="e.g. 1428 Nkulumane 12"
                  value={address}
                  maxLength={500}
                  onChange={(event) => setAddress(event.target.value)}
                />
                <span className="meta">Only shared with the worker you hire.</span>
              </div>
            )}

            <div className="field" style={{ marginTop: 18 }}>
              <label htmlFor="su-emergency" className="field__label">
                Emergency contact number (optional)
              </label>
              <input
                id="su-emergency"
                className="input"
                type="tel"
                inputMode="tel"
                placeholder="e.g. 77 200 0111"
                value={emergencyPhone}
                maxLength={20}
                onChange={(event) => setEmergencyPhone(event.target.value)}
              />
              <span className="meta">
                {isWorker
                  ? "Someone we can call if something goes wrong on a job."
                  : "Someone we can call if something goes wrong at a job."}
              </span>
            </div>
          </>
        )}

        {error && (
          <p id="su-error" className="field-error" role="alert" style={{ marginTop: 12 }}>
            {error}
          </p>
        )}

        <div className="spacer" style={{ minHeight: 32 }} />

        <button type="submit" className="btn btn--primary btn--cta" disabled={isSigningIn}>
          {isSigningIn
            ? isLogin
              ? "Logging you in…"
              : "Creating your account…"
            : isLogin
              ? "Log in"
              : "Create account"}
          {!isSigningIn && <Icon name="arrowRight" size={18} strokeWidth={2.2} />}
        </button>

        <p
          className="meta meta--secondary"
          style={{ marginTop: 16, textAlign: "center", fontSize: 14 }}
        >
          {isLogin ? "Don't have an account? " : "Already have an account? "}
          <Link
            href={isLogin ? `/signup?role=${roleParam}` : `/signup?mode=login&role=${roleParam}`}
            style={{ fontWeight: 600 }}
            onClick={() => setValidationError(null)}
          >
            {isLogin ? "Create account" : "Log in"}
          </Link>
        </p>

        <p className="meta" style={{ marginTop: 10, textAlign: "center", lineHeight: 1.5 }}>
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
