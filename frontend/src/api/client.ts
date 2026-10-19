import type { ApiErrorBody } from "./types";

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000"
).replace(/\/$/, "");
const DEFAULT_TIMEOUT_MS = 10_000;

export class ApiError extends Error {
  readonly status: number;
  readonly code?: string;
  readonly fieldErrors: Record<string, string>;

  constructor(message: string, status = 0, body: ApiErrorBody = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = body.code;
    this.fieldErrors = body.field_errors ?? {};
  }
}

export async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(
    () => controller.abort(),
    DEFAULT_TIMEOUT_MS,
  );
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        Accept: "application/json",
        ...(init.body ? { "Content-Type": "application/json" } : {}),
        ...init.headers,
      },
      signal: init.signal ?? controller.signal,
    });
    const isJson =
      response.headers.get("content-type")?.includes("application/json") ??
      false;
    const body: ApiErrorBody = isJson
      ? ((await response.json()) as ApiErrorBody)
      : {};
    if (!response.ok)
      throw new ApiError(
        body.message ?? `Request failed (${response.status}).`,
        response.status,
        body,
      );
    return body as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === "AbortError")
      throw new ApiError("The server took too long to respond.");
    throw new ApiError(
      "Unable to reach the GlucoCare API. Check that the backend is running.",
    );
  } finally {
    window.clearTimeout(timeout);
  }
}
