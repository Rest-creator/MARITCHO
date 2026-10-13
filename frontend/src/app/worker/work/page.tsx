import type { Metadata } from "next";

import { MyWorkScreen, type WorkTab } from "@/features/worker/MyWorkScreen";

export const metadata: Metadata = { title: "My work" };

type Props = { searchParams: Promise<Record<string, string | string[] | undefined>> };

const TABS: readonly WorkTab[] = ["offers", "active", "done"];

export default async function MyWorkPage({ searchParams }: Props) {
  const { tab } = await searchParams;
  const initialTab = TABS.find((item) => item === tab) ?? "active";
  return <MyWorkScreen initialTab={initialTab} />;
}
