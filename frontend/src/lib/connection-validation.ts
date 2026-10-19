export const required = (label: string) => (value: string) =>
  value.trim() ? undefined : `${label} is required.`;

const HOST_RE = /^[A-Za-z0-9._:\-[\]]+$/;

export function validateHost(value: string): string | undefined {
  const trimmed = value.trim();
  if (!trimmed) return "Host is required.";
  if (trimmed.length > 255 || !HOST_RE.test(trimmed)) return "Host contains invalid characters.";
  return undefined;
}

export function validatePort(value: string): string | undefined {
  if (!value.trim()) return "Port is required.";
  const n = Number(value);
  if (!Number.isInteger(n) || n < 1 || n > 65535) return "Port must be a number between 1 and 65535.";
  return undefined;
}