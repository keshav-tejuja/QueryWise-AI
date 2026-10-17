export interface ReadyResponse {
  status: string;
  database: string;
}

export async function getReady(): Promise<ReadyResponse> {
  const response = await fetch("/api/v1/health/ready");
  const body = (await response.json()) as ReadyResponse;
  if (!response.ok) {
    throw Object.assign(new Error("Backend not ready"), { body });
  }
  return body;
}