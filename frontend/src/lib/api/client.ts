import { API_BASE_URL } from "@/lib/config";

/** An error returned by the API, carrying the backend's `{error: {code, message}}`. */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(message: string, status: number, code = "request_failed") {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

type ValidationDetail = { loc?: (string | number)[]; msg?: string }[];

function messageFromBody(body: unknown, status: number): { message: string; code: string } {
  if (body && typeof body === "object") {
    const record = body as Record<string, unknown>;
    const error = record.error as { message?: string; code?: string } | undefined;
    if (error?.message) {
      return { message: error.message, code: error.code ?? "request_failed" };
    }
    const detail = record.detail as string | ValidationDetail | undefined;
    if (typeof detail === "string") {
      return { message: detail, code: "request_failed" };
    }
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0];
      return {
        message: first?.msg ?? "The request was rejected.",
        code: "validation_error",
      };
    }
  }
  return { message: `Request failed (${status}).`, code: "request_failed" };
}

/** Thin typed fetch wrapper: 204 becomes `undefined`, errors become `ApiError`. */
export async function apiRequest<T>(
  path: string,
  init: RequestInit & { json?: unknown } = {},
): Promise<T> {
  const { json, headers, ...rest } = init;
  const isForm = rest.body instanceof FormData;

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...rest,
      headers: {
        ...(json !== undefined && !isForm ? { "Content-Type": "application/json" } : {}),
        ...headers,
      },
      body: json !== undefined ? JSON.stringify(json) : rest.body,
      cache: "no-store",
    });
  } catch {
    throw new ApiError(
      "Can't reach the API. Is the backend running on port 8000?",
      0,
      "network_error",
    );
  }

  if (response.status === 204) return undefined as T;

  const text = await response.text();
  let body: unknown = null;
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      body = null;
    }
  }

  if (!response.ok) {
    const { message, code } = messageFromBody(body, response.status);
    throw new ApiError(message, response.status, code);
  }

  return body as T;
}

/** Small helper for the `?user_id=` query the API still expects (no JWT yet). */
export function withUser(path: string, userId: string): string {
  const separator = path.includes("?") ? "&" : "?";
  return `${path}${separator}user_id=${encodeURIComponent(userId)}`;
}
