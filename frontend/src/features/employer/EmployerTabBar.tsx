import { TabBar, type TabItem } from "@/components/ui/TabBar";

const EMPLOYER_TABS: readonly TabItem[] = [
  { href: "/employer", label: "Home", icon: "home" },
  { href: "/employer/jobs", label: "My jobs", icon: "briefcase", matches: ["/employer/jobs/"] },
  { href: "/employer/messages", label: "Messages", icon: "chat" },
  { href: "/employer/account", label: "Account", icon: "user" },
];

export function EmployerTabBar() {
  return <TabBar items={EMPLOYER_TABS} ariaLabel="Employer navigation" />;
}
