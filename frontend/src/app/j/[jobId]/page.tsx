import type { Metadata } from "next";

import { SharedJobScreen } from "@/features/jobs/SharedJobScreen";
import { jobSharePath, shareDescription, shareHeadline } from "@/features/jobs/job-share";
import { getJobShare, publicOrigin } from "@/server/job-share";

type Props = { params: Promise<{ jobId: string }> };

/**
 * Public, sign-in-free page behind a shared job link. Its Open Graph and
 * Twitter tags make WhatsApp, LinkedIn, Facebook and X show a card with the
 * job and the suburb (the image comes from ./opengraph-image.tsx).
 */
export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { jobId } = await params;
  const [result, origin] = await Promise.all([getJobShare(jobId), publicOrigin()]);
  if (result.kind !== "found") {
    return { title: "Job on Maritcho", robots: { index: false } };
  }
  const title = shareHeadline(result.job);
  const description = result.job.is_open
    ? shareDescription(result.job)
    : "This job has been filled. Find more jobs near you on Maritcho.";
  const url = `${origin}${jobSharePath(jobId)}`;
  return {
    metadataBase: new URL(origin),
    title,
    description,
    alternates: { canonical: url },
    // Shared links are for people, not search engines: the job closes soon.
    robots: { index: false, follow: true },
    openGraph: { type: "website", siteName: "Maritcho", url, title, description, locale: "en_ZW" },
    twitter: { card: "summary_large_image", title, description },
  };
}

export default async function SharedJobPage({ params }: Props) {
  const { jobId } = await params;
  const result = await getJobShare(jobId);
  return (
    <SharedJobScreen
      job={result.kind === "found" ? result.job : null}
      isUnavailable={result.kind === "unavailable"}
    />
  );
}
