const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function validateEmail(value: string): string | undefined {
  const trimmed = value.trim();
  if (!trimmed) return "Email is required.";
  if (!EMAIL_RE.test(trimmed)) return "Enter a valid email address.";
  return undefined;
}

// Mirrors the backend rule (10 to 128 characters); the server remains the authority.
export function validatePassword(value: string): string | undefined {
  if (!value) return "Password is required.";
  if (value.length < 10) return "Use at least 10 characters.";
  if (value.length > 128) return "Use at most 128 characters.";
  return undefined;
}

export function validateDisplayName(value: string): string | undefined {
  const trimmed = value.trim();
  if (!trimmed) return "Name is required.";
  if (trimmed.length > 80) return "Use at most 80 characters.";
  return undefined;
}