import type { z } from "zod";

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }

  get isUnauthorized(): boolean {
    return this.status === 401;
  }

  /** 0 = the request never reached the server; 503 = the BFF could not reach the backend. */
  get isNetwork(): boolean {
    return this.status === 0 || this.status === 503;
  }
}

type Method = "GET" | "POST" | "PUT" | "DELETE";

interface RequestOptions<S extends z.ZodType | undefined> {
  method?: Method;
  body?: unknown;
  schema?: S;
  signal?: AbortSignal;
}

type Parsed<S> = S extends z.ZodType ? z.output<S> : void;

function detailMessage(payload: unknown, fallback: string): string {
  if (typeof payload === "object" && payload !== null && "detail" in payload) {
    const detail = (payload as { detail: unknown }).detail;
    if (typeof detail === "string") {
      return detail;
    }
    // FastAPI 422s carry a list of { msg } validation issues.
    if (Array.isArray(detail) && detail.length > 0) {
      const first: unknown = detail[0];
      if (typeof first === "object" && first !== null && "msg" in first) {
        return String((first as { msg: unknown }).msg);
      }
    }
  }
  return fallback;
}

function fallbackMessage(status: number): string {
  if (status === 401) return "Please sign in again.";
  if (status === 403) return "You can't do that with this account.";
  if (status === 404) return "We couldn't find that.";
  if (status >= 500) return "Maricho is having trouble. Please try again soon.";
  return "Something went wrong. Please try again.";
}

/** The ApiError for a failed BFF response, using the backend's `detail` when it has one. */
export function apiErrorFrom(status: number, payload: unknown): ApiError {
  return new ApiError(detailMessage(payload, fallbackMessage(status)), status);
}

/**
 * Same-origin request to the BFF (`/api/...` → FastAPI). Throws ApiError so
 * TanStack Query can drive retry, pause-while-offline and error states.
 */
export async function apiRequest<S extends z.ZodType | undefined = undefined>(
  path: string,
  { method = "GET", body, schema, signal }: RequestOptions<S> = {},
): Promise<Parsed<S>> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, {
      method,
      signal,
      credentials: "same-origin",
      headers: body === undefined ? undefined : { "content-type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch (error: unknown) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    throw new ApiError("You're offline. We'll try again when you're connected.", 0);
  }

  const payload: unknown = response.status === 204 ? null : await response.json().catch(() => null);

  if (!response.ok) {
    throw apiErrorFrom(response.status, payload);
  }
  if (schema === undefined) {
    return undefined as Parsed<S>;
  }
  return schema.parse(payload) as Parsed<S>;
}
