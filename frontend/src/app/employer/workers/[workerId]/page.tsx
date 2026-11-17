import type { Metadata } from "next";

import { WorkerPublicProfileScreen } from "@/features/employer/WorkerPublicProfileScreen";

export const metadata: Metadata = { title: "Worker profile" };

type Props = {
  params: Promise<{ workerId: string }>;
  searchParams: Promise<{ suburb?: string }>;
};

export default async function WorkerPublicProfilePage({ params, searchParams }: Props) {
  const { workerId } = await params;
  const { suburb } = await searchParams;
  return <WorkerPublicProfileScreen workerId={workerId} initialSuburb={suburb ?? null} />;
}
