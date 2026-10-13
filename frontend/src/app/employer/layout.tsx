import type { ReactNode } from "react";

import { RoleGate } from "@/features/accounts/RoleGate";

type Props = { children: ReactNode };

export default function EmployerLayout({ children }: Props) {
  return <RoleGate role="BUYER">{children}</RoleGate>;
}
