"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { Icon } from "@/components/ui/Icon";
import { Screen } from "@/components/ui/Screen";
import { homeFor, useSession } from "@/core/session/SessionProvider";

/** Design 1 · Welcome – choose your path. */
export function WelcomeScreen() {
  const { user } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (user !== null) router.replace(homeFor(user.role));
  }, [user, router]);

  return (
    <Screen bodyClassName="screen__body--welcome">
      <div className="brand">
        <div className="brand__mark">
          <Icon name="wrench" strokeWidth={2} />
        </div>
        Maricho
      </div>

      <div style={{ marginTop: 64 }}>
        <h1 className="title title--hero">Your skills are your CV.</h1>
        <p className="lead" style={{ marginTop: 14, fontSize: 16 }}>
          Find trusted hands for any job nearby, or get hired for the work you already know how to
          do.
        </p>
      </div>

      <div className="label" style={{ marginTop: 44, fontSize: 13 }}>
        How will you use Maricho?
      </div>
      <div className="stack" style={{ marginTop: 12, gap: 12 }}>
        <Link href="/signup?role=buyer" className="path-card">
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
        <Link href="/signup?role=worker" className="path-card">
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
        Already have an account?{" "}
        <Link href="/signup?mode=login" style={{ fontWeight: 600 }}>
          Log in
        </Link>
      </p>
    </Screen>
  );
}
