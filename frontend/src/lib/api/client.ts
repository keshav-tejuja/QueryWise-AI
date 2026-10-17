import type { TokenResponse } from "./types";

const API_BASE = "/api/v1";

export interface ApiErrorDetail {
  field: string;
  message: string;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly requestId?: string;
  readonly details?: ApiErrorDetail[];

  constructor(
    status: number,
    code: string,
    message: string,
    requestId?: string,
    details?: ApiErrorDetail[],
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.requestId = requestId;
    this.details = details;
  }
}

// The access token lives in memory only: never localStorage/sessionStorage.
let accessToken: string | null = null;
let refreshInFlight: Promise<TokenResponse | null> | null = null;
let sessionExpiredHandler: (() => void) | null = null;

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function setSessionExpiredHandler(handler: (() => void) | null): void {
  sessionExpiredHandler = handler;
}

async function toApiError(response: Response): Promise<ApiError> {
  try {
    const body = await response.json();
    const err = body?.error;
    if (err) {
      return new ApiError(
        response.status,
        err.code ?? "error",
        err.message ?? "Request failed.",
        err.request_id,
        err.details,
      );
    }
  } catch {
    // fall through to the generic error
  }
  return new ApiError(response.status, "unknown_error", "Something went wrong. Please try again.");
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  /** Attach the bearer token and try a silent refresh on 401. */
  auth?: boolean;
  retryOnUnauthorized?: boolean;
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, auth = true, retryOnUnauthorized = true } = options;

  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (auth && accessToken) headers["Authorization"] = `Bearer ${accessToken}`;

  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, "network_error", "Cannot reach the server. Check your connection and try again.");
  }

  if (response.status === 401 && auth && retryOnUnauthorized) {
    const session = await refreshSession();
    if (session) {
      return request<T>(path, { ...options, retryOnUnauthorized: false });
    }
    sessionExpiredHandler?.();
  }

  if (!response.ok) throw await toApiError(response);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

/**
 * Silent refresh using the httpOnly cookie. Concurrent callers share ONE in-flight request:
 * the backend rotates refresh tokens and treats a reused token as theft, so two parallel
 * refreshes with the same cookie would otherwise sign the user out everywhere.
 */
export function refreshSession(): Promise<TokenResponse | null> {
  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const data = await request<TokenResponse>("/auth/refresh", { method: "POST", auth: false });
        accessToken = data.access_token;
        return data;
      } catch {
        accessToken = null;
        return null;
      } finally {
        refreshInFlight = null;
      }
    })();
  }
  return refreshInFlight;
}