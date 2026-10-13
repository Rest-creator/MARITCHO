import type { Metadata } from "next";

import { ApplicantsScreen } from "@/features/jobs/ApplicantsScreen";

export const metadata: Metadata = { title: "Offers" };

type Props = { params: Promise<{ jobId: string }> };

export default async function ApplicantsPage({ params }: Props) {
  const { jobId } = await params;
  return <ApplicantsScreen jobId={jobId} />;
}
