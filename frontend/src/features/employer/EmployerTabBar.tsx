"use client";

import { TabBar, type TabItem } from "@/components/ui/TabBar";
import { unreadTotal, useUnreadDocumentTitle, useUnreadMessages } from "@/features/messaging/hooks";

const MESSAGES_HREF = "/employer/messages";

const EMPLOYER_TABS: readonly TabItem[] = [
  { href: "/employer", label: "Home", icon: "home" },
  {
    href: "/employer/workers",
    label: "Workers",
    icon: "users",
    matches: ["/employer/workers/"],
  },
  { href: "/employer/jobs", label: "My jobs", icon: "briefcase", matches: ["/employer/jobs/"] },
  { href: MESSAGES_HREF, label: "Messages", icon: "chat" },
  { href: "/employer/account", label: "Account", icon: "user" },
];

export function EmployerTabBar() {
  const unread: number = unreadTotal(useUnreadMessages().data);
  useUnreadDocumentTitle(unread);
  const items: TabItem[] = EMPLOYER_TABS.map((item) =>
    item.href === MESSAGES_HREF ? { ...item, badge: unread } : item,
  );
  return <TabBar items={items} ariaLabel="Employer navigation" />;
}
