import type { Metadata } from "next";

import { PolicyScreen } from "@/features/accounts/PolicyScreen";

export const metadata: Metadata = { title: "Terms and Conditions" };

export default function TermsPage() {
  return <PolicyScreen title="Terms and Conditions" />;
}
