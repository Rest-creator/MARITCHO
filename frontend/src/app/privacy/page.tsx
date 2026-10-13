import type { Metadata } from "next";

import { PolicyScreen } from "@/features/accounts/PolicyScreen";

export const metadata: Metadata = { title: "Privacy Policy" };

export default function PrivacyPage() {
  return <PolicyScreen title="Privacy Policy" />;
}
