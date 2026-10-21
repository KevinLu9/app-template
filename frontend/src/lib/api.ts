/**
 * The only way the frontend talks to the backend. Same-origin, JSON in and out.
 * Authentication is handled by Databricks (session cookie); never add tokens here.
 */

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly requestId?: string;

  constructor(status: number, code: string, message: string, requestId?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.requestId = requestId;
  }
}

type ErrorBody = { error?: { code?: string; message?: string; request_id?: string } };

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...init,
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...init.headers,
    },
  });

  const isJson = response.headers.get("Content-Type")?.includes("application/json") ?? false;

  // An expired Databricks session redirects API calls to the login page (HTML, not JSON).
  if (response.redirected || (!isJson && response.status !== 204)) {
    throw new ApiError(401, "session_expired", "Your session has expired. Reload the page.");
  }

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as ErrorBody;
    throw new ApiError(
      response.status,
      body.error?.code ?? "error",
      body.error?.message ?? response.statusText,
      body.error?.request_id,
    );
  }

  return (response.status === 204 ? undefined : await response.json()) as T;
}

export const apiGet = <T>(path: string) => api<T>(path);

export const apiSend = <T>(
  method: "POST" | "PATCH" | "PUT" | "DELETE",
  path: string,
  body?: unknown,
) => api<T>(path, { method, body: body === undefined ? undefined : JSON.stringify(body) });
