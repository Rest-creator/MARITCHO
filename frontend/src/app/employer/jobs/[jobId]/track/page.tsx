import type { Metadata } from "next";

import { JobTrackingScreen } from "@/features/jobs/JobTrackingScreen";

export const metadata: Metadata = { title: "Job progress" };

type Props = { params: Promise<{ jobId: string }> };

export default async function JobTrackingPage({ params }: Props) {
  const { jobId } = await params;
  return <JobTrackingScreen jobId={jobId} />;
}
