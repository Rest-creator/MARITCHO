import type { ReactNode } from "react";

import { Icon, type IconName } from "@/components/ui/Icon";

type EmptyProps = { title: string; children?: ReactNode; icon?: IconName; action?: ReactNode };

export function EmptyState({ title, children, icon = "search", action }: EmptyProps) {
  return (
    <div className="empty">
      <Icon name={icon} size={24} />
      <div className="empty__title">{title}</div>
      {children && <div>{children}</div>}
      {action}
    </div>
  );
}

type ErrorProps = { message: string; onRetry?: () => void };

export function ErrorState({ message, onRetry }: ErrorProps) {
  return (
    <div className="banner banner--danger" role="alert">
      <div className="grow">{message}</div>
      {onRetry && (
        <button type="button" className="text-link" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}

type SkeletonProps = { height?: number; count?: number };

export function Skeleton({ height = 120, count = 1 }: SkeletonProps) {
  return (
    <div className="stack" aria-busy="true" aria-label="Loading">
      {Array.from({ length: count }, (_, index) => (
        <div key={index} className="skeleton" style={{ height }} />
      ))}
    </div>
  );
}
