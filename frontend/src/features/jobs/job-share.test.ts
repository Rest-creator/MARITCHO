import { describe, expect, it } from "vitest";

import { jobShareSchema } from "@/core/api/schemas";
import {
  jobSharePath,
  jobShareUrl,
  shareDescription,
  shareHeadline,
  shareMessage,
  shareTargets,
  shareTradeLabel,
  workerJobPath,
} from "@/features/jobs/job-share";

const JOB = {
  trade: "PLUMBING",
  suburb: "Nkulumane",
  needed_by: "TODAY",
  pricing_mode: "FIXED",
} as const;
const ID = "3f2b8c1e-1d2a-4b9e-9a77-0c6c3e5f8d11";

describe("job share links", () => {
  it("builds a short public path and absolute url", () => {
    expect(jobSharePath(ID)).toBe(`/j/${ID}`);
    expect(jobShareUrl("https://maricho.restk.tech/", ID)).toBe(
      `https://maricho.restk.tech/j/${ID}`,
    );
    expect(workerJobPath(ID)).toBe(`/worker/jobs/${ID}`);
  });

  it("says only the job and the place", () => {
    expect(shareHeadline(JOB)).toBe("Plumber needed in Nkulumane");
    expect(shareDescription(JOB)).toBe(
      "Needed today · Fixed price. See the details and send your price on Maritcho.",
    );
    expect(shareHeadline({ trade: "PLUMBING", suburb: "  " })).toBe("Plumber needed");
    expect(shareDescription({ trade: "PLUMBING", suburb: "Luveve" })).toBe(
      "See the details and send your price on Maritcho.",
    );
  });

  it("labels trades the app doesn't list yet", () => {
    expect(shareTradeLabel("GENERAL_MAINTENANCE")).toBe("General maintenance");
    expect(shareTradeLabel("ELECTRICAL")).toBe("Electrician");
  });

  it("fills each app's share screen with the link", () => {
    const url = `https://maricho.restk.tech/j/${ID}`;
    const targets = shareTargets(JOB, url);
    expect(targets.map((target) => target.id)).toEqual(["whatsapp", "facebook", "linkedin", "x"]);
    const whatsapp = targets.find((target) => target.id === "whatsapp");
    expect(decodeURIComponent(whatsapp?.href.split("text=")[1] ?? "")).toBe(shareMessage(JOB, url));
    const linkedin = targets.find((target) => target.id === "linkedin");
    expect(linkedin?.href).toBe(
      `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`,
    );
  });

  it("parses the public teaser, including trades outside Stage One", () => {
    const parsed = jobShareSchema.parse({
      job_id: ID,
      trade: "ROOFING",
      suburb: "Nkulumane",
      needed_by: "THIS_WEEK",
      pricing_mode: "NEGOTIABLE",
      is_open: true,
      created_at: "2026-11-25T08:00:00",
    });
    expect(parsed.created_at).toBe("2026-11-25T08:00:00Z");
    expect(shareHeadline(parsed)).toBe("Roofing needed in Nkulumane");
  });
});
