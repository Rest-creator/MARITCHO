import { tradeSchema, type NeededBy, type PricingMode } from "@/core/api/schemas";
import { tradeLabel } from "@/core/format/trades";

/*
 * Shareable job links (WEB-024). A shared link reveals only the kind of work
 * and the suburb — enough for a WhatsApp/LinkedIn/Facebook preview to make
 * someone curious. Everything else (description, price, address, photos)
 * stays in the app, so the link drives people to sign in.
 */

/** The fields a share card is built from; the app's Job and the public teaser both fit. */
export interface ShareableJob {
  trade: string;
  suburb: string;
  needed_by?: NeededBy | undefined;
  pricing_mode?: PricingMode | undefined;
}

/** Short public path: `/j/<job id>`. */
export function jobSharePath(jobId: string): string {
  return `/j/${encodeURIComponent(jobId)}`;
}

export function jobShareUrl(origin: string, jobId: string): string {
  return `${origin.replace(/\/+$/, "")}${jobSharePath(jobId)}`;
}

/** Where the full job lives in the app; a shared link sends people here. */
export function workerJobPath(jobId: string): string {
  return `/worker/jobs/${encodeURIComponent(jobId)}`;
}

/** "Plumber", or a readable fallback for trades the app doesn't list yet. */
export function shareTradeLabel(trade: string): string {
  const known = tradeSchema.safeParse(trade);
  if (known.success) return tradeLabel(known.data);
  const words = trade.toLowerCase().replace(/_/g, " ").trim();
  return words === "" ? "Worker" : words.charAt(0).toUpperCase() + words.slice(1);
}

/** "Plumber needed in Nkulumane" — the preview title. */
export function shareHeadline(job: ShareableJob): string {
  const where = job.suburb.trim();
  const who = `${shareTradeLabel(job.trade)} needed`;
  return where === "" ? who : `${who} in ${where}`;
}

const NEEDED_BY_LABEL: Record<NeededBy, string> = {
  TODAY: "Needed today",
  THIS_WEEK: "Needed this week",
  FLEXIBLE: "Flexible timing",
};

const PRICING_LABEL: Record<PricingMode, string> = {
  FIXED: "Fixed price",
  NEGOTIABLE: "Price negotiable",
  AFTER_VISIT: "Price agreed after a visit",
};

/** "Needed today · Fixed price" — small facts that don't give the job away. */
export function shareFacts(job: ShareableJob): string[] {
  const facts: string[] = [];
  if (job.needed_by) facts.push(NEEDED_BY_LABEL[job.needed_by]);
  if (job.pricing_mode) facts.push(PRICING_LABEL[job.pricing_mode]);
  return facts;
}

/** The preview description under the headline. */
export function shareDescription(job: ShareableJob): string {
  const facts = shareFacts(job);
  const lead = facts.length > 0 ? `${facts.join(" · ")}. ` : "";
  return `${lead}See the details and send your price on Maritcho.`;
}

/** The message that goes with the link (WhatsApp, SMS, a post). */
export function shareMessage(job: ShareableJob, url: string): string {
  return `${shareHeadline(job)} — ${shareDescription(job)}\n${url}`;
}

export interface ShareTarget {
  id: "whatsapp" | "facebook" | "linkedin" | "x";
  label: string;
  href: string;
}

/** Links that open each app's own share screen with the job link filled in. */
export function shareTargets(job: ShareableJob, url: string): ShareTarget[] {
  const encodedUrl = encodeURIComponent(url);
  return [
    {
      id: "whatsapp",
      label: "WhatsApp",
      href: `https://wa.me/?text=${encodeURIComponent(shareMessage(job, url))}`,
    },
    {
      id: "facebook",
      label: "Facebook",
      href: `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`,
    },
    {
      id: "linkedin",
      label: "LinkedIn",
      href: `https://www.linkedin.com/sharing/share-offsite/?url=${encodedUrl}`,
    },
    {
      id: "x",
      label: "X",
      href: `https://x.com/intent/post?text=${encodeURIComponent(shareHeadline(job))}&url=${encodedUrl}`,
    },
  ];
}
