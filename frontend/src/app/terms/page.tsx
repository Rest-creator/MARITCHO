import type { Metadata } from "next";

import { PolicyScreen } from "@/features/accounts/PolicyScreen";

export const metadata: Metadata = { title: "Terms" };

export default function TermsPage() {
  return <PolicyScreen title="Terms" />;
}
