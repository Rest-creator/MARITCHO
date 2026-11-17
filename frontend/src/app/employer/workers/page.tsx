import type { Metadata } from "next";

import { WorkersScreen } from "@/features/employer/WorkersScreen";

export const metadata: Metadata = { title: "Workers near you" };

export default function WorkersPage() {
  return <WorkersScreen />;
}
