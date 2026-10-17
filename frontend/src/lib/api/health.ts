export type BackendState = "ready" | "degraded" | "unreachable";

export interface BackendStatus {
  status: BackendState;
  database: string;
}

/** Never throws: an unreachable backend is a status, not an exception. */
export async function getBackendStatus(): Promise<BackendStatus> {
  try {
    const response = await fetch("/api/v1/health/ready");
    const body = await response.json();
    if (response.ok) return { status: "ready", database: body.database ?? "ok" };
    return { status: "degraded", database: body.database ?? "unavailable" };
  } catch {
    return { status: "unreachable", database: "unknown" };
  }
}