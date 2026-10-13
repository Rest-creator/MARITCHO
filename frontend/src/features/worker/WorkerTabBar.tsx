import { TabBar, type TabItem } from "@/components/ui/TabBar";

const WORKER_TABS: readonly TabItem[] = [
  { href: "/worker", label: "Find jobs", icon: "search", matches: ["/worker/jobs/"] },
  { href: "/worker/work", label: "My work", icon: "briefcase" },
  { href: "/worker/messages", label: "Messages", icon: "chat" },
  { href: "/worker/account", label: "My profile", icon: "user" },
];

export function WorkerTabBar() {
  return <TabBar items={WORKER_TABS} ariaLabel="Worker navigation" />;
}
