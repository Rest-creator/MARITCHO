import type { Role, User } from "@/core/api/schemas";

/**
 * One account can hire and find work. `user.role` is the side the person is
 * using right now (navigation, home screen); `user.roles` is every side the
 * account has unlocked. Older sessions without `roles` have just `role`.
 */
export function canActAs(user: Pick<User, "role" | "roles"> | null, role: Role): boolean {
  if (user === null) return false;
  return user.role === role || (user.roles ?? []).includes(role);
}

/** True when the account has both the hiring and the working side. */
export function hasBothSides(user: Pick<User, "role" | "roles"> | null): boolean {
  return canActAs(user, "BUYER") && canActAs(user, "WORKER");
}
