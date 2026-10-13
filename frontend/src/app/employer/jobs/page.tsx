import type { Metadata } from "next";

import { MyJobsScreen } from "@/features/employer/MyJobsScreen";

export const metadata: Metadata = { title: "My jobs" };

export default function MyJobsPage() {
  return <MyJobsScreen />;
}
