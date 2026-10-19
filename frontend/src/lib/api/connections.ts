import { request } from "./client";

export type SslMode = "disable" | "prefer" | "require" | "verify-ca" | "verify-full";
export type ConnectionStatus = "untested" | "connected" | "error" | "disconnected";

export interface Connection {
  id: string;
  name: string;
  host: string;
  port: number;
  database: string;
  username: string;
  ssl_mode: SslMode;
  status: ConnectionStatus;
  last_tested_at: string | null;
  created_at: string;
}

export interface CheckResult {
  ok: boolean;
  code: string;
  message: string;
  latency_ms: number | null;
  server_version: string | null;
  read_only: boolean | null;
  warnings: string[];
}

export interface ConnectionWithCheck {
  connection: Connection;
  check: CheckResult | null;
}

export interface ConnectionInput {
  name: string;
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  ssl_mode: SslMode;
}
export type ConnectionTestInput = Omit<ConnectionInput, "name">;
export type ConnectionPatch = Partial<ConnectionInput>;

export const connectionsApi = {
  list: () => request<Connection[]>("/connections"),
  testParams: (input: ConnectionTestInput) =>
    request<CheckResult>("/connections/test", { method: "POST", body: input }),
  create: (input: ConnectionInput) =>
    request<ConnectionWithCheck>("/connections", { method: "POST", body: input }),
  update: (id: string, input: ConnectionPatch) =>
    request<ConnectionWithCheck>(`/connections/${id}`, { method: "PATCH", body: input }),
  test: (id: string) => request<ConnectionWithCheck>(`/connections/${id}/test`, { method: "POST" }),
  disconnect: (id: string) => request<Connection>(`/connections/${id}/disconnect`, { method: "POST" }),
  remove: (id: string) => request<void>(`/connections/${id}`, { method: "DELETE" }),
};