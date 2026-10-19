import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import type { CheckResult } from "@/lib/api/connections";

export function CheckResultView({ check }: { check: CheckResult }) {
  const details = [
    check.latency_ms != null ? `${check.latency_ms} ms` : null,
    check.server_version ? `PostgreSQL ${check.server_version}` : null,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <div className="space-y-2">
      {check.ok ? (
        <Alert variant="success">
          <p className="font-medium">Connection successful</p>
          {details && <p className="text-xs opacity-90">{details}</p>}
        </Alert>
      ) : (
        <Alert variant="destructive">{check.message}</Alert>
      )}
      {check.ok && check.read_only !== null && (
        <Badge variant={check.read_only ? "success" : "warning"}>
          {check.read_only ? "Read-only role" : "Role can modify data"}
        </Badge>
      )}
      {check.warnings.map((warning) => (
        <Alert key={warning} variant="warning">
          {warning}
        </Alert>
      ))}
    </div>
  );
}