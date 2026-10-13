import type { ReactNode } from "react";

import { RoleGate } from "@/features/accounts/RoleGate";

type Props = { children: ReactNode };

export default function WorkerLayout({ children }: Props) {
  return <RoleGate role="WORKER">{children}</RoleGate>;
}
