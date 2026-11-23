"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { BrandLogo } from "@/components/ui/BrandLogo";
import { Icon } from "@/components/ui/Icon";
import { Screen } from "@/components/ui/Screen";
import { updateProfile, useLocalProfile } from "@/core/session/profile-store";
import { homeFor, useSession } from "@/core/session/SessionProvider";
import { HowItWorks } from "@/features/onboarding/HowItWorks";

/** Design 1 · Welcome – choose your path. */
export function WelcomeScreen() {
  const { user } = useSession();
  const profile = useLocalProfile();
  const router = useRouter();

  useEffect(() => {
    if (user !== null) router.replace(homeFor(user.role));
  }, [user, router]);

  return (
    <Screen bodyClassName="screen__body--welcome">
      <div className="row row--between">
        <BrandLogo />
        <button
          type="button"
          className="icon-btn"
          aria-label={
            profile.theme === "light"
              ? "Switch to dark theme"
              : "Switch to White & Blue light theme"
          }
          title={profile.theme === "light" ? "Dark (Default)" : "White & Blue"}
          onClick={() => updateProfile({ theme: profile.theme === "light" ? "dark" : "light" })}
        >
          <Icon name={profile.theme === "light" ? "moon" : "sun"} size={18} />
        </button>
      </div>

      <div style={{ marginTop: 64 }}>
        <h1 className="title title--hero">Your skills are your CV.</h1>
        <p className="lead" style={{ marginTop: 14, fontSize: 16 }}>
          Find trusted hands for any job nearby, or get hired for the work you already know how to
          do.
        </p>
      </div>

      <div className="label" style={{ marginTop: 44, fontSize: 13 }}>
        How will you use Maritcho?
      </div>
      <div className="stack path-grid" style={{ marginTop: 12, gap: 12 }}>
        <Link href="/signup?mode=login&role=buyer" className="path-card">
          <div className="icon-tile icon-tile--lg icon-tile--amber icon-tile--edged">
            <Icon name="home" size={22} strokeWidth={1.75} />
          </div>
          <div className="grow">
            <div style={{ fontSize: 17, fontWeight: 700 }}>I need work done</div>
            <div
              className="meta meta--secondary"
              style={{ marginTop: 4, fontSize: 13, lineHeight: 1.45 }}
            >
              Plumbing, repairs, solar, welding, building and more
            </div>
          </div>
          <Icon name="chevronRight" className="text-muted" strokeWidth={2} />
        </Link>
        <Link href="/signup?mode=login&role=worker" className="path-card">
          <div className="icon-tile icon-tile--lg icon-tile--emerald icon-tile--edged">
            <Icon name="briefcase" size={22} strokeWidth={1.75} />
          </div>
          <div className="grow">
            <div style={{ fontSize: 17, fontWeight: 700 }}>I&apos;m looking for work</div>
            <div
              className="meta meta--secondary"
              style={{ marginTop: 4, fontSize: 13, lineHeight: 1.45 }}
            >
              Get jobs for what you can do — no certificates needed
            </div>
          </div>
          <Icon name="chevronRight" strokeWidth={2} />
        </Link>
      </div>

      <div style={{ marginTop: 28 }}>
        <HowItWorks />
      </div>

      <div className="spacer" style={{ minHeight: 32 }} />

      <div className="banner banner--quiet">
        <span className="text-emerald" style={{ display: "flex" }}>
          <Icon name="shieldCheck" size={18} strokeWidth={1.75} />
        </span>
        <span>Every finished job leaves a review you can trust — for both sides.</span>
      </div>
      <p
        className="meta meta--secondary"
        style={{ marginTop: 20, textAlign: "center", fontSize: 14 }}
      >
        Don&apos;t have an account?{" "}
        <Link href="/signup" style={{ fontWeight: 600 }}>
          Create account
        </Link>
      </p>
      <p className="meta" style={{ marginTop: 10, textAlign: "center", fontSize: 12 }}>
        <Link href="/terms" style={{ color: "var(--text-secondary)", textDecoration: "underline" }}>
          Terms and Conditions
        </Link>{" "}
        ·{" "}
        <Link
          href="/privacy"
          style={{ color: "var(--text-secondary)", textDecoration: "underline" }}
        >
          Privacy Policy
        </Link>
      </p>
    </Screen>
  );
}
