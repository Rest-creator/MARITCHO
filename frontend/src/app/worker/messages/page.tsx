import type { Metadata } from "next";

import { WorkerMessagesScreen } from "@/features/worker/WorkerMessagesScreen";

export const metadata: Metadata = { title: "Messages" };

export default function WorkerMessagesPage() {
  return <WorkerMessagesScreen />;
}
