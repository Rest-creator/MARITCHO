"use client";

import { useState, type ReactNode } from "react";
import Link from "next/link";

import { Avatar } from "@/components/ui/Avatar";
import { Icon } from "@/components/ui/Icon";
import { Screen } from "@/components/ui/Screen";
import { formatLocalPhone } from "@/core/format/format";
import { updateProfile, useLocalProfile } from "@/core/session/profile-store";
import { useSession } from "@/core/session/SessionProvider";

type Props = { tabBar: ReactNode };

export function AccountScreen({ tabBar }: Props) {
  const { user, signOut } = useSession();
  const profile = useLocalProfile();
  const [name, setName] = useState(profile.name);
  const isWorker = user?.role === "WORKER";
  const displayName = profile.name || "Your account";

  return (
    <Screen glow={isWorker ? "worker" : "employer"} hasTabBar>
      <h1 className="title title--page">{isWorker ? "My profile" : "Account"}</h1>

      <div className="card row">
        <Avatar name={displayName} seed={user?.id ?? displayName} size="md" />
        <div className="grow">
          <div style={{ fontSize: 16, fontWeight: 700 }}>{displayName}</div>
          <div className="meta">
            +263 {formatLocalPhone(user?.phone ?? profile.phone)} ·{" "}
            {isWorker ? "Finds work" : "Hires help"}
          </div>
        </div>
      </div>

      <form
        className="card stack"
        onSubmit={(event) => {
          event.preventDefault();
          updateProfile({ name: name.trim() });
        }}
      >
        <div className="field">
          <label htmlFor="acc-name" className="field__label">
            Name shown in the app
          </label>
          <input
            id="acc-name"
            className="input"
            value={name}
            maxLength={80}
            onChange={(event) => setName(event.target.value)}
          />
        </div>
        <button type="submit" className="btn btn--soft" disabled={name.trim() === profile.name}>
          Save name
        </button>
        <p className="meta">Saved on this phone.</p>
      </form>

      {isWorker && (
        <Link href="/worker/skills" className="list-row">
          <div className="icon-tile icon-tile--emerald">
            <Icon name="briefcase" />
          </div>
          <div className="grow">
            <div style={{ fontWeight: 700 }}>Skills & travel distance</div>
            <div className="meta">Change what work you’re shown</div>
          </div>
          <Icon name="chevronRight" strokeWidth={2} />
        </Link>
      )}

      <button type="button" className="btn btn--block" onClick={() => void signOut()}>
        <Icon name="logout" size={18} />
        Sign out
      </button>
      {tabBar}
    </Screen>
  );
}
