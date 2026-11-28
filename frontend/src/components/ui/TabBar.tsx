"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { BrandLogo } from "@/components/ui/BrandLogo";
import { Icon, type IconName } from "@/components/ui/Icon";

export interface TabItem {
  href: string;
  label: string;
  icon: IconName;
  /** Extra path prefixes that should light this tab up. */
  matches?: readonly string[];
  /** Unread count shown on the icon (hidden when 0). */
  badge?: number;
}

function badgeText(count: number): string {
  return count > 99 ? "99+" : String(count);
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
      <div className="tabbar__brand">
        <BrandLogo isDecorative />
      </div>
      {items.map((item) => {
        const badge: number = item.badge ?? 0;
        return (
          <Link
            key={item.href}
            href={item.href}
            className="tabbar__item"
            aria-current={isTabActive(pathname, item) ? "page" : undefined}
            aria-label={badge > 0 ? `${item.label}, ${badgeText(badge)} unread` : undefined}
          >
            <span className="tabbar__icon">
              <Icon name={item.icon} size={22} strokeWidth={1.8} />
              {badge > 0 && (
                <span className="tabbar__badge" aria-hidden="true">
                  {badgeText(badge)}
                </span>
              )}
            </span>
            <span>{item.label}</span>
          </Link>
        );
      })}

      <div className="tabbar__footer" style={{ marginTop: "auto", paddingTop: 16 }}>
        <a
          href="/downloads/maritcho.apk"
          download="maritcho.apk"
          className="tabbar__item tabbar__item--download"
          title="Download Maritcho Mobile App"
          aria-label="Download Maritcho Mobile App"
        >
          <span className="tabbar__icon">
            <Icon name="smartphone" size={22} strokeWidth={1.8} />
          </span>
          <span>Get Mobile App</span>
        </a>
      </div>
    </nav>
  );
}
