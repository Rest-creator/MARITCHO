import type { Metadata } from "next";

import { AccountScreen } from "@/features/accounts/AccountScreen";
import { EmployerTabBar } from "@/features/employer/EmployerTabBar";

export const metadata: Metadata = { title: "Account" };

export default function EmployerAccountPage() {
  return <AccountScreen tabBar={<EmployerTabBar />} />;
}
