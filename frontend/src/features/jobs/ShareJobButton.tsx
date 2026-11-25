"use client";

import { useEffect, useRef, useState } from "react";

import { Icon } from "@/components/ui/Icon";
import { Sheet } from "@/components/ui/Sheet";
import {
  jobShareUrl,
  shareDescription,
  shareHeadline,
  shareTargets,
  type ShareableJob,
} from "@/features/jobs/job-share";

type Props = {
  jobId: string;
  job: ShareableJob;
  /** "Share job" button text; icon-only when false. */
  hasLabel?: boolean;
};

/**
 * Share a job link that shows only the job and the suburb (WEB-024). On
 * phones this opens the system share sheet (WhatsApp, Facebook, LinkedIn…);
 * elsewhere a small sheet offers the same apps and "Copy link".
 */
export function ShareJobButton({ jobId, job, hasLabel = true }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const resetTimer = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (resetTimer.current !== null) window.clearTimeout(resetTimer.current);
    };
  }, []);

  function currentUrl(): string {
    return jobShareUrl(window.location.origin, jobId);
  }

  async function handleShare(): Promise<void> {
    const url = currentUrl();
    if (typeof navigator.share === "function") {
      try {
        await navigator.share({ title: shareHeadline(job), text: shareDescription(job), url });
        return;
      } catch (failure: unknown) {
        // Closing the share sheet is not an error worth showing.
        if (failure instanceof DOMException && failure.name === "AbortError") return;
      }
    }
    setIsOpen(true);
  }

  async function copyLink(): Promise<void> {
    try {
      await navigator.clipboard.writeText(currentUrl());
      setCopied(true);
      if (resetTimer.current !== null) window.clearTimeout(resetTimer.current);
      resetTimer.current = window.setTimeout(() => setCopied(false), 2500);
    } catch {
      setCopied(false);
    }
  }

  const url = isOpen ? currentUrl() : "";

  return (
    <>
      <button
        type="button"
        className={hasLabel ? "btn btn--sm btn--soft" : "icon-btn"}
        aria-label="Share this job"
        onClick={() => void handleShare()}
      >
        <Icon name="share" size={hasLabel ? 14 : 18} />
        {hasLabel && "Share"}
      </button>

      <Sheet title="Share this job" isOpen={isOpen} onClose={() => setIsOpen(false)} isFitContent>
        <p className="meta" style={{ lineHeight: 1.5 }}>
          The link shows only <strong>{shareHeadline(job)}</strong>. People open Maritcho to see the
          details and reply.
        </p>
        <div className="btn-grid" style={{ marginTop: 14 }}>
          {shareTargets(job, url).map((target) => (
            <a
              key={target.id}
              href={target.href}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn--soft"
            >
              {target.label}
            </a>
          ))}
        </div>
        <div className="row" style={{ gap: 8, marginTop: 14, alignItems: "center" }}>
          <input
            className="input grow"
            readOnly
            value={url}
            aria-label="Job link"
            onFocus={(event) => event.currentTarget.select()}
          />
          <button type="button" className="btn btn--sm" onClick={() => void copyLink()}>
            <Icon name={copied ? "check" : "link"} size={14} />
            {copied ? "Copied" : "Copy link"}
          </button>
        </div>
      </Sheet>
    </>
  );
}
