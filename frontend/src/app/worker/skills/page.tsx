import type { Metadata } from "next";

import { WorkerSkillsScreen } from "@/features/worker/WorkerSkillsScreen";

export const metadata: Metadata = { title: "Your skills" };

export default function WorkerSkillsPage() {
  return <WorkerSkillsScreen />;
}
