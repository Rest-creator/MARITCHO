import type { Metadata } from "next";

import { WorkerReviewsScreen } from "@/features/worker/WorkerReviewsScreen";

export const metadata: Metadata = { title: "Your reviews" };

export default function WorkerReviewsPage() {
  return <WorkerReviewsScreen />;
}
