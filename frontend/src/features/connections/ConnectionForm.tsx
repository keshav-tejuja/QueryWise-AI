import { useState, type FormEvent } from "react";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { FormField } from "@/components/ui/form-field";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { ApiError } from "@/lib/api/client";
import type {
  CheckResult,
  Connection,
  ConnectionPatch,
  ConnectionTestInput,
  SslMode,
} from "@/lib/api/connections";
import { required, validateHost, validatePort } from "@/lib/connection-validation";
import { CheckResultView } from "./CheckResultView";

interface Values {
  name: string;
  host: string;
  port: string;
  database: string;
  username: string;
  password: string;
  ssl_mode: SslMode;
}
type Errors = Partial<Record<keyof Values, string>>;

const SSL_OPTIONS: { value: SslMode; label: string }[] = [
  { value: "prefer", label: "Prefer (use SSL if available)" },
  { value: "disable", label: "Disable (no SSL, local development only)" },
  { value: "require", label: "Require (encrypted, certificate not verified)" },
  { value: "verify-ca", label: "Verify CA" },
  { value: "verify-full", label: "Verify full (recommended for production)" },
];

const EMPTY: Values = { name: "", host: "", port: "5432", database: "", username: "", password: "", ssl_mode: "prefer" };

// Dev-only demo database from docker-compose.yml: not shown in production builds.
const DEMO: Values = {
  name: "Sample e-commerce",
  host: "sampledb",
  port: "5432",
  database: "sample",
  username: "qw_readonly",
  password: "readonly_dev_pw",
  ssl_mode: "prefer",
};

function validate(values: Values, isEdit: boolean, includeName: boolean): Errors {
  const errors: Errors = {
    host: validateHost(values.host),
    port: validatePort(values.port),
    database: required("Database")(values.database),
    username: required("Username")(values.username),
  };
  if (includeName) errors.name = required("Name")(values.name);
  if (!isEdit) errors.password = required("Password")(values.password);
  return Object.fromEntries(Object.entries(errors).filter(([, message]) => message)) as Errors;
}

interface ConnectionFormProps {
  initial?: Connection;
  onSubmit: (payload: ConnectionPatch) => Promise<void>;
  onTest?: (payload: ConnectionTestInput) => Promise<CheckResult>;
  onCancel: () => void;
}

export function ConnectionForm({ initial, onSubmit, onTest, onCancel }: ConnectionFormProps) {
  const isEdit = Boolean(initial);
  const [values, setValues] = useState<Values>(
    initial
      ? {
          name: initial.name,
          host: initial.host,
          port: String(initial.port),
          database: initial.database,
          username: initial.username,
          password: "",
          ssl_mode: initial.ssl_mode,
        }
      : EMPTY,
  );
  const [errors, setErrors] = useState<Errors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [check, setCheck] = useState<CheckResult | null>(null);
  const [pending, setPending] = useState(false);
  const [testing, setTesting] = useState(false);

  function update<K extends keyof Values>(field: K, value: Values[K]) {
    setValues((prev) => ({ ...prev, [field]: value }));
    setCheck(null); // a result no longer applies once the inputs change
  }

  function payloadFrom(): ConnectionPatch {
    return {
      name: values.name.trim(),
      host: values.host.trim(),
      port: Number(values.port),
      database: values.database.trim(),
      username: values.username.trim(),
      ssl_mode: values.ssl_mode,
      ...(values.password ? { password: values.password } : {}),
    };
  }

  async function handleTest() {
    if (!onTest) return;
    setFormError(null);
    const next = validate(values, false, false);
    setErrors(next);
    if (Object.keys(next).length > 0) return;
    setTesting(true);
    try {
      const { name: _name, ...rest } = payloadFrom();
      setCheck(await onTest(rest as ConnectionTestInput));
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Something went wrong. Please try again.");
    } finally {
      setTesting(false);
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setFormError(null);
    const next = validate(values, isEdit, true);
    setErrors(next);
    if (Object.keys(next).length > 0) return;
    setPending(true);
    try {
      await onSubmit(payloadFrom());
    } catch (error) {
      if (error instanceof ApiError && error.code === "connection_name_taken") {
        setErrors({ name: error.message });
      } else {
        setFormError(error instanceof ApiError ? error.message : "Something went wrong. Please try again.");
      }
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4">
      {import.meta.env.DEV && !isEdit && (
        <div className="rounded-md border border-dashed border-border p-3 text-sm text-muted-foreground">
          <p>
            <strong className="text-foreground">Local demo database.</strong> From inside Docker the host is{" "}
            <code>sampledb</code> on port 5432. From Windows tools it's <code>localhost:5434</code>.
          </p>
          <Button
            variant="outline"
            size="sm"
            className="mt-2"
            onClick={() => {
              setValues(DEMO);
              setErrors({});
              setCheck(null);
            }}
          >
            Use demo database
          </Button>
        </div>
      )}

      {formError && <Alert variant="destructive">{formError}</Alert>}

      <FormField id="conn-name" label="Connection name" value={values.name} error={errors.name}
        onChange={(e) => update("name", e.target.value)} />
      <div className="grid gap-4 sm:grid-cols-[1fr_7rem]">
        <FormField id="conn-host" label="Host" autoComplete="off" value={values.host} error={errors.host}
          onChange={(e) => update("host", e.target.value)} />
        <FormField id="conn-port" label="Port" inputMode="numeric" value={values.port} error={errors.port}
          onChange={(e) => update("port", e.target.value)} />
      </div>
      <FormField id="conn-database" label="Database" autoComplete="off" value={values.database}
        error={errors.database} onChange={(e) => update("database", e.target.value)} />
      <FormField id="conn-username" label="Username" autoComplete="off" value={values.username}
        error={errors.username} onChange={(e) => update("username", e.target.value)} />
      <FormField id="conn-password" label="Password" type="password" autoComplete="new-password"
        value={values.password} error={errors.password}
        hint={isEdit ? "Leave blank to keep the saved password." : undefined}
        onChange={(e) => update("password", e.target.value)} />
      <div className="space-y-2">
        <Label htmlFor="conn-ssl">SSL mode</Label>
        <Select id="conn-ssl" value={values.ssl_mode} onChange={(e) => update("ssl_mode", e.target.value as SslMode)}>
          {SSL_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
      </div>

      {check && <CheckResultView check={check} />}

      <div className="flex flex-wrap justify-end gap-2 pt-2">
        <Button variant="ghost" onClick={onCancel}>
          Cancel
        </Button>
        {onTest && !isEdit && (
          <Button variant="outline" onClick={() => void handleTest()} loading={testing}>
            Test connection
          </Button>
        )}
        <Button type="submit" loading={pending}>
          {isEdit ? "Save changes" : "Save connection"}
        </Button>
      </div>
    </form>
  );
}