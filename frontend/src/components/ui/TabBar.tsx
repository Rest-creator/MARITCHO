"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Icon, type IconName } from "@/components/ui/Icon";

export interface TabItem {
  href: string;
  label: string;
  icon: IconName;
  /** Extra path prefixes that should light this tab up. */
  matches?: readonly string[];
}

type Props = { items: readonly TabItem[]; ariaLabel: string };

export function isTabActive(pathname: string, item: TabItem): boolean {
  if (pathname === item.href) return true;
  return (item.matches ?? []).some((prefix) => pathname.startsWith(prefix));
}

export function TabBar({ items, ariaLabel }: Props) {
  const pathname = usePathname();
  return (
    <nav className="tabbar" aria-label={ariaLabel}>
      {items.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className="tabbar__item"
          aria-current={isTabActive(pathname, item) ? "page" : undefined}
        >
          <Icon name={item.icon} size={22} strokeWidth={1.8} />
          <span>{item.label}</span>
        </Link>
      ))}
    </nav>
  );
}
