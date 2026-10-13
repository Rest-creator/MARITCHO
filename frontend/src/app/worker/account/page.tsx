import type { Metadata } from "next";

import { AccountScreen } from "@/features/accounts/AccountScreen";
import { WorkerTabBar } from "@/features/worker/WorkerTabBar";

export const metadata: Metadata = { title: "My profile" };

export default function WorkerAccountPage() {
  return <AccountScreen tabBar={<WorkerTabBar />} />;
}
