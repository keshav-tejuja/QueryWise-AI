import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { Connection } from "@/lib/api/connections";
import { ConnectionForm } from "./ConnectionForm";

const okCheck = {
  ok: true, code: "ok", message: "Connection successful.", latency_ms: 12,
  server_version: "16.4", read_only: true, warnings: [],
};

it("shows validation errors and does not submit an empty form", async () => {
  const onSubmit = vi.fn();
  render(<ConnectionForm onSubmit={onSubmit} onCancel={vi.fn()} />);
  await userEvent.click(screen.getByRole("button", { name: /save connection/i }));
  expect(screen.getByText("Name is required.")).toBeInTheDocument();
  expect(screen.getByText("Host is required.")).toBeInTheDocument();
  expect(screen.getByText("Password is required.")).toBeInTheDocument();
  expect(onSubmit).not.toHaveBeenCalled();
});

it("submits the demo values with a numeric port", async () => {
  const onSubmit = vi.fn().mockResolvedValue(undefined);
  render(<ConnectionForm onSubmit={onSubmit} onCancel={vi.fn()} />);
  await userEvent.click(screen.getByRole("button", { name: /use demo database/i }));
  await userEvent.click(screen.getByRole("button", { name: /save connection/i }));
  expect(onSubmit).toHaveBeenCalledWith(
    expect.objectContaining({ host: "sampledb", port: 5432, ssl_mode: "prefer", password: "readonly_dev_pw" }),
  );
});

it("validates before testing, then shows the result", async () => {
  const onTest = vi.fn().mockResolvedValue(okCheck);
  render(<ConnectionForm onSubmit={vi.fn()} onTest={onTest} onCancel={vi.fn()} />);
  await userEvent.click(screen.getByRole("button", { name: /test connection/i }));
  expect(onTest).not.toHaveBeenCalled();
  await userEvent.click(screen.getByRole("button", { name: /use demo database/i }));
  await userEvent.click(screen.getByRole("button", { name: /test connection/i }));
  expect(onTest).toHaveBeenCalledTimes(1);
  expect(await screen.findByText("Connection successful")).toBeInTheDocument();
});

it("edit mode keeps the saved password when the field is blank", async () => {
  const initial: Connection = {
    id: "1", name: "Demo", host: "sampledb", port: 5432, database: "sample", username: "qw_readonly",
    ssl_mode: "prefer", status: "connected", last_tested_at: null, created_at: "2026-01-01T00:00:00Z",
  };
  const onSubmit = vi.fn().mockResolvedValue(undefined);
  render(<ConnectionForm initial={initial} onSubmit={onSubmit} onCancel={vi.fn()} />);
  await userEvent.click(screen.getByRole("button", { name: /save changes/i }));
  expect(onSubmit).toHaveBeenCalledTimes(1);
  expect(onSubmit.mock.calls[0][0]).not.toHaveProperty("password");
});