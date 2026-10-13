import type { Metadata } from "next";

import { EmployerMessagesScreen } from "@/features/employer/EmployerMessagesScreen";

export const metadata: Metadata = { title: "Messages" };

export default function EmployerMessagesPage() {
  return <EmployerMessagesScreen />;
}
