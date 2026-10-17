import { useState, type FormEvent } from "react";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { FormField } from "@/components/ui/form-field";
import { ApiError } from "@/lib/api/client";
import { validateDisplayName, validateEmail, validatePassword } from "@/lib/validation";

interface RegisterFormProps {
  onSubmit: (displayName: string, email: string, password: string) => Promise<void>;
}

type FieldErrors = { displayName?: string; email?: string; password?: string };

export function RegisterForm({ onSubmit }: RegisterFormProps) {
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setFormError(null);
    const next: FieldErrors = {
      displayName: validateDisplayName(displayName),
      email: validateEmail(email),
      password: validatePassword(password),
    };
    setErrors(next);
    if (next.displayName || next.email || next.password) return;

    setPending(true);
    try {
      await onSubmit(displayName.trim(), email.trim(), password);
    } catch (error) {
      if (error instanceof ApiError && error.code === "email_taken") {
        setErrors({ email: error.message });
      } else if (error instanceof ApiError && error.details?.length) {
        const serverErrors: FieldErrors = {};
        for (const detail of error.details) {
          if (detail.field === "email") serverErrors.email = detail.message;
          if (detail.field === "password") serverErrors.password = detail.message;
          if (detail.field === "display_name") serverErrors.displayName = detail.message;
        }
        setErrors(serverErrors);
      } else {
        setFormError(error instanceof ApiError ? error.message : "Something went wrong. Please try again.");
      }
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4">
      {formError && <Alert variant="destructive">{formError}</Alert>}
      <FormField
        id="register-name"
        label="Name"
        autoComplete="name"
        value={displayName}
        onChange={(e) => setDisplayName(e.target.value)}
        error={errors.displayName}
      />
      <FormField
        id="register-email"
        label="Email"
        type="email"
        autoComplete="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        error={errors.email}
      />
      <FormField
        id="register-password"
        label="Password"
        type="password"
        autoComplete="new-password"
        hint="At least 10 characters."
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        error={errors.password}
      />
      <Button type="submit" className="w-full" loading={pending}>
        Create account
      </Button>
    </form>
  );
}