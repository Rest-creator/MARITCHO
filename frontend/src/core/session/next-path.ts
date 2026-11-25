/**
 * Where to go after signing in (`?next=`), e.g. back to a shared job.
 * Only same-site paths are accepted — never `//evil.com` or `https://…` —
 * so the parameter can't be used to bounce people to another website.
 */
export function safeNextPath(value: string | string[] | null | undefined): string | null {
  const raw = Array.isArray(value) ? value[0] : value;
  if (typeof raw !== "string" || raw.length > 512) return null;
  if (!raw.startsWith("/") || raw.startsWith("//") || raw.includes("\\")) return null;
  // Control characters (tabs, newlines) can turn "/\t/evil.com" into "//evil.com".
  if (/[\u0000-\u001f\u007f]/.test(raw)) return null;
  return raw;
}

/** Appends `next` to a path, if there is one. */
export function withNext(path: string, next: string | null): string {
  if (next === null) return path;
  const separator = path.includes("?") ? "&" : "?";
  return `${path}${separator}next=${encodeURIComponent(next)}`;
}
