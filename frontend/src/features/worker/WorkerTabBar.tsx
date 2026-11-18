"use client";

import { TabBar, type TabItem } from "@/components/ui/TabBar";
import { unreadTotal, useUnreadDocumentTitle, useUnreadMessages } from "@/features/messaging/hooks";

const MESSAGES_HREF = "/worker/messages";

const WORKER_TABS: readonly TabItem[] = [
  { href: "/worker", label: "Find jobs", icon: "search", matches: ["/worker/jobs/"] },
  { href: "/worker/work", label: "My work", icon: "briefcase" },
  { href: MESSAGES_HREF, label: "Messages", icon: "chat" },
  { href: "/worker/account", label: "My profile", icon: "user" },
];

export function WorkerTabBar() {
  const unread: number = unreadTotal(useUnreadMessages().data);
  useUnreadDocumentTitle(unread);
  const items: TabItem[] = WORKER_TABS.map((item) =>
    item.href === MESSAGES_HREF ? { ...item, badge: unread } : item,
  );
  return <TabBar items={items} ariaLabel="Worker navigation" />;
}
