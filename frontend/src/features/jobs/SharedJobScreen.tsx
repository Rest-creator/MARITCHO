"use client";

import Link from "next/link";

import { BrandLogo } from "@/components/ui/BrandLogo";
import { Icon } from "@/components/ui/Icon";
import { Screen } from "@/components/ui/Screen";
import type { JobShare } from "@/core/api/schemas";
import { formatRelativeTime } from "@/core/format/format";
import { tradeIcon } from "@/core/format/trades";
import { tradeSchema } from "@/core/api/schemas";
import { withNext } from "@/core/session/next-path";
import { useSession } from "@/core/session/SessionProvider";
import {
  shareFacts,
  shareHeadline,
  shareTradeLabel,
  workerJobPath,
} from "@/features/jobs/job-share";

type Props = { job: JobShare | null; isUnavailable?: boolean };

/**
 * Landing page for a shared job link (`/j/<id>`). Shows only the kind of
 * work and the suburb; the description, price and address are in the app,
 * so the one clear action is to open it there.
 */
export function SharedJobScreen({ job, isUnavailable = false }: Props) {
  const { user } = useSession();

  if (job === null) {
    return (
      <Screen glow="worker">
        <BrandLogo />
        <div className="empty" style={{ marginTop: 48 }}>
          <Icon name="briefcase" size={24} />
          <div style={{ fontWeight: 700 }}>
            {isUnavailable ? "We couldn't load this job" : "This job is no longer available"}
          </div>
          <div className="meta">
            {isUnavailable
              ? "Check your connection and try again."
              : "There are more jobs near you on Maritcho."}
          </div>
        </div>
        <Link href={user ? "/worker" : "/signup?role=worker"} className="btn btn--block">
          Find jobs near you
        </Link>
      </Screen>
    );
  }

  const destination = workerJobPath(job.job_id);
  const known = tradeSchema.safeParse(job.trade);
  const facts = shareFacts(job);
  const signUpHref = withNext("/signup?role=worker", destination);
  const logInHref = withNext("/signup?mode=login&role=worker", destination);

  return (
    <Screen glow="worker">
      <BrandLogo />

      <section className="card" style={{ marginTop: 28, padding: "20px 18px" }}>
        <div className="row" style={{ gap: 12, alignItems: "center" }}>
          <div className="icon-tile icon-tile--lg icon-tile--emerald icon-tile--edged">
            <Icon name={known.success ? tradeIcon(known.data) : "wrench"} size={22} />
          </div>
          <div className="grow">
            <div className="label">{shareTradeLabel(job.trade)}</div>
            <h1 className="title" style={{ marginTop: 2 }}>
              {shareHeadline(job)}
            </h1>
          </div>
        </div>

        <div className="row" style={{ gap: 6, marginTop: 14, alignItems: "center" }}>
          <Icon name="pin" size={16} />
          <span style={{ fontWeight: 600 }}>{job.suburb}</span>
          {job.created_at && (
            <span className="meta">· Posted {formatRelativeTime(job.created_at)}</span>
          )}
        </div>

        {facts.length > 0 && (
          <div className="chip-list" style={{ marginTop: 12 }}>
            {facts.map((fact) => (
              <span key={fact} className="tag">
                {fact}
              </span>
            ))}
          </div>
        )}
      </section>

      {job.is_open ? (
        <>
          <div className="banner banner--quiet" style={{ borderRadius: 16 }}>
            <Icon name="shieldCheck" size={18} />
            <span className="grow">
              What the client needs, the budget and how to reply are in the Maritcho app.
            </span>
          </div>
          {user ? (
            <Link href={destination} className="btn btn--block">
              See the job details
              <Icon name="arrowRight" size={18} />
            </Link>
          ) : (
            <div className="stack" style={{ gap: 10 }}>
              <Link href={signUpHref} className="btn btn--block">
                Sign up to see details and apply
                <Icon name="arrowRight" size={18} />
              </Link>
              <Link href={logInHref} className="btn btn--soft btn--block">
                I already have an account
              </Link>
            </div>
          )}
        </>
      ) : (
        <>
          <div className="banner banner--quiet" style={{ borderRadius: 16 }} role="status">
            <Icon name="check" size={18} />
            <span className="grow">This job has been filled. There are more jobs on Maritcho.</span>
          </div>
          <Link href={user ? "/worker" : "/signup?role=worker"} className="btn btn--block">
            Find jobs near you
          </Link>
        </>
      )}
    </Screen>
  );
}
